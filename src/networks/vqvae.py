import torch.nn as nn
import torch.nn.functional as F


class ResidualLayer(nn.Module):
    """
    One residual layer inputs:
    - in_dim : the input dimension
    - h_dim : the hidden layer dimension
    - res_h_dim : the hidden dimension of the residual block
    """

    def __init__(self, in_dim, h_dim, res_h_dim):
        super(ResidualLayer, self).__init__()
        self.res_block = nn.Sequential(
            nn.ReLU(True),
            nn.Conv2d(
                in_dim, res_h_dim, kernel_size=3, stride=1, padding=1, bias=False
            ),
            nn.ReLU(True),
            nn.Conv2d(res_h_dim, h_dim, kernel_size=1, stride=1, bias=False),
        )

    def forward(self, x):
        x = x + self.res_block(x)
        return x


class ResidualStack(nn.Module):
    """
    A stack of residual layers inputs:
    - in_dim : the input dimension
    - h_dim : the hidden layer dimension
    - res_h_dim : the hidden dimension of the residual block
    - n_res_layers : number of layers to stack
    """

    def __init__(self, in_dim, h_dim, res_h_dim, n_res_layers):
        super(ResidualStack, self).__init__()
        self.n_res_layers = n_res_layers
        self.stack = nn.ModuleList(
            [ResidualLayer(in_dim, h_dim, res_h_dim)] * n_res_layers
        )

    def forward(self, x):
        for layer in self.stack:
            x = layer(x)
        x = F.relu(x)
        return x


class Encoder(nn.Module):
    """
    This is the q_theta (z|x) network. Given a data sample x q_theta
    maps to the latent space x -> z.
    For a VQ VAE, q_theta outputs parameters of a categorical distribution.
    Inputs:
    - in_dim : the input dimension
    - h_dim : the hidden layer dimension
    - res_h_dim : the hidden dimension of the residual block
    - n_res_layers : number of layers to stack
    """

    def __init__(self, input_channel, output_channel, n_res_layers=3, res_h_dim=128):
        super(Encoder, self).__init__()
        kernel = 4
        stride = 2
        self.conv_stack = nn.Sequential(
            nn.Conv2d(
                input_channel,
                output_channel // 2,
                kernel_size=kernel,
                stride=stride,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                output_channel // 2,
                output_channel,
                kernel_size=kernel,
                stride=stride,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                output_channel,
                output_channel,
                kernel_size=kernel - 1,
                stride=stride - 1,
                padding=1,
            ),
            ResidualStack(output_channel, output_channel, res_h_dim, n_res_layers),
        )

    def forward(self, x):
        return self.conv_stack(x)


class Decoder(nn.Module):
    """
    This is the p_phi (x|z) network. Given a latent sample z p_phi
    maps back to the original space z -> x.
    Inputs:
    - in_dim : the input dimension
    - h_dim : the hidden layer dimension
    - res_h_dim : the hidden dimension of the residual block
    - n_res_layers : number of layers to stack
    """

    def __init__(
        self, input_channel, output_channel, h_dim=128, n_res_layers=3, res_h_dim=128
    ):
        super(Decoder, self).__init__()
        kernel = 4
        stride = 2

        self.inverse_conv_stack = nn.Sequential(
            nn.ConvTranspose2d(
                input_channel,
                h_dim,
                kernel_size=kernel - 1,
                stride=stride - 1,
                padding=1,
            ),
            ResidualStack(h_dim, h_dim, res_h_dim, n_res_layers),
            nn.ConvTranspose2d(
                h_dim, h_dim // 2, kernel_size=kernel, stride=stride, padding=1
            ),
            nn.ReLU(),
            nn.ConvTranspose2d(
                h_dim // 2, output_channel, kernel_size=kernel, stride=stride, padding=1
            ),
        )

    def forward(self, x):
        return self.inverse_conv_stack(x)
