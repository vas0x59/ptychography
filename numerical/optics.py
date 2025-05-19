import torch
import numpy as np
import tools



def Hz(z, k, kx, ky):
    return torch.exp(-1j * z * torch.sqrt(k**2 - (kx**2 - ky**2)))


def cringe_source(sigma, kx0, ky0, kx, ky):
    A0 = torch.exp(-((kx-kx0)**2 + (ky-ky0)**2)/sigma**2)
    A0 /=torch.max(A0)
    U0 = torch.fft.ifft2(A0)
    U0 /=torch.max(torch.abs(U0))
    U0 = torch.fft.fftshift(U0)
    return U0


def init_space(size, N):
    x = y = torch.tensor(np.linspace(-size/2, size/2, N)).cuda()
    d = x[1] - x[0]
    wx, wy = torch.meshgrid(x, y, indexing='xy')
    fx_ = torch.fft.fftfreq(len(x), d=d).cuda() *2*torch.pi
    kx, ky = torch.meshgrid(fx_, fx_, indexing='xy')
    return d, wx, wy, kx, ky



def multi_mode_grf_phase_shift(modes, size):
    rnd = torch.ones([size, size], device="cuda", dtype=torch.complex64)
    for cor, ampl in modes:
        rnd *= torch.exp(tools.gaussian_random_field( (size, size), cor).cuda()*ampl*1j)
    return rnd
