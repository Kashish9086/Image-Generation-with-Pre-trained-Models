import torch
from omegaconf import OmegaConf
from .base import BaseModel, ValidationResult
from hydra.utils import instantiate
from src.utils.losses import adversarial_loss

class GAN(BaseModel):
    def __init__(
        self,
        datamodule: OmegaConf,
        netG: OmegaConf,
        netD: OmegaConf,
        latent_dim: int = 100,
        loss_mode: str = "vanilla",
        lrG: float = 2e-4,
        lrD: float = 2e-4,
        b1: float = 0.5,
        b2: float = 0.999,
    ):
        super().__init__(datamodule)
        self.save_hyperparameters()
        self.netG = instantiate(netG, input_channel=latent_dim, output_channel=self.channels)
        self.netD = instantiate(netD, input_channel=self.channels, output_channel=1)
        self.automatic_optimization = False

    def forward(self, z):
        output = self.netG(z)
        output = output.reshape(z.shape[0], self.channels, self.height, self.width)
        return output

    def configure_optimizers(self):
        lrG, lrD = self.hparams.lrG, self.hparams.lrD
        b1, b2 = self.hparams.b1, self.hparams.b2
        opt_g = torch.optim.Adam(self.netG.parameters(), lr=lrG, betas=(b1, b2))
        opt_d = torch.optim.Adam(self.netD.parameters(), lr=lrD, betas=(b1, b2))
        return [opt_g, opt_d]

    def training_step(self, batch, batch_idx):
        imgs, _ = batch  # (N, C, H, W)
        N, C, H, W = imgs.shape
        z = torch.randn(N, self.hparams.latent_dim).to(self.device)

        opt_g, opt_d = self.optimizers()

        if batch_idx % 2 == 0:
            self.toggle_optimizer(opt_g)
            fake_imgs = self.netG(z)
            pred_fake = self.netD(fake_imgs)
            g_loss = adversarial_loss(pred_fake, target_is_real=True, loss_mode=self.hparams.loss_mode)
            
            opt_g.zero_grad()
            self.manual_backward(g_loss)
            opt_g.step()
            self.untoggle_optimizer(opt_g)

            self.log("train_loss/g_loss", g_loss)
        else:
            self.toggle_optimizer(opt_d)
            pred_real = self.netD(imgs)
            real_loss = adversarial_loss(pred_real, target_is_real=True, loss_mode=self.hparams.loss_mode)

            fake_imgs = self.netG(z).detach()
            pred_fake = self.netD(fake_imgs)
            fake_loss = adversarial_loss(pred_fake, target_is_real=False, loss_mode=self.hparams.loss_mode)

            d_loss = (real_loss + fake_loss) / 2

            opt_d.zero_grad()
            self.manual_backward(d_loss)
            opt_d.step()
            self.untoggle_optimizer(d_loss)

            self.log("train_loss/d_loss", d_loss)
            self.log("train_log/pred_real", pred_real.mean())
            self.log("train_log/pred_fake", pred_fake.mean())

    def validation_step(self, batch, batch_idx):
        img, _ = batch
        z = torch.randn(img.shape[0], self.hparams.latent_dim).to(self.device)
        fake_imgs = self.forward(z)
        return ValidationResult(real_image=img, fake_image=fake_imgs)
