import torch
import numpy as np

import torch.nn.functional as F

def compute_phase_gradient(F_cplx):
    """
    F_cplx: complex tensor of shape [H, W] with |F| ≈ 1 (unit magnitude)
    Returns: tensor of shape [2, H, W] representing ∇θ (gradient of phase)
    """
    assert torch.is_complex(F_cplx), "Input must be a complex tensor"

    # Define finite difference kernels (central difference)
    dx_kernel = torch.tensor([[0, 0, 0],
                              [-0.5, 0, 0.5],
                              [0, 0, 0]], dtype=torch.float32).reshape(1, 1, 3, 3)
    dy_kernel = torch.tensor([[0, -0.5, 0],
                              [0, 0, 0],
                              [0, 0.5, 0]], dtype=torch.float32).reshape(1, 1, 3, 3)

    dx_kernel = dx_kernel.to(F_cplx.device)
    dy_kernel = dy_kernel.to(F_cplx.device)

    # Separate real and imaginary parts
    real = F_cplx.real.unsqueeze(0).unsqueeze(0)  # shape [1, 1, H, W]
    imag = F_cplx.imag.unsqueeze(0).unsqueeze(0)

    # Apply convolution to compute ∂F/∂x and ∂F/∂y
    dFdx = F.conv2d(real, dx_kernel, padding=1) + 1j * F.conv2d(imag, dx_kernel, padding=1)
    dFdy = F.conv2d(real, dy_kernel, padding=1) + 1j * F.conv2d(imag, dy_kernel, padding=1)

    dFdx = dFdx.squeeze()
    dFdy = dFdy.squeeze()

    # Compute ∇θ = Im(∇F / F)
    grad_x = torch.imag(dFdx / F_cplx)
    grad_y = torch.imag(dFdy / F_cplx)

    # Stack as [2, H, W]: [∂θ/∂x, ∂θ/∂y]
    grad_phase = torch.stack([grad_x, grad_y], dim=0)
    return grad_phase


def gaussian_random_field(shape, correlation_length, device="cuda", dtype=torch.float32):
    """
    Generate a 2D Gaussian random field with a specified correlation length using PyTorch.

    Parameters:
    - shape: tuple of ints (nx, ny), the dimensions of the field
    - correlation_length: float, the Gaussian correlation length in grid units
    - device: torch device (e.g., 'cpu' or 'cuda'), default None uses CPU
    - dtype: torch dtype, default torch.float32

    Returns:
    - field: 2D torch tensor of shape (nx, ny)
    """
    # Determine device
    if device is None:
        device = torch.device('cpu')

    nx, ny = shape
    # Create frequency grids
    fx = torch.fft.fftfreq(nx, d=1.0, device=device, dtype=dtype)
    fy = torch.fft.fftfreq(ny, d=1.0, device=device, dtype=dtype)
    kx, ky = torch.meshgrid(fx, fy, indexing='ij')
    k2 = kx**2 + ky**2

    # Gaussian power spectrum in frequency domain
    power_spectrum = torch.exp(-0.5 * k2 * (correlation_length**2))

    # White noise in spatial domain
    noise = torch.randn((nx, ny), device=device, dtype=dtype)
    noise_fft = torch.fft.fft2(noise)

    # Impose power spectrum and inverse FFT
    field_fft = noise_fft * torch.sqrt(power_spectrum)
    field = torch.fft.ifft2(field_fft).real

    return field/field.abs().max()