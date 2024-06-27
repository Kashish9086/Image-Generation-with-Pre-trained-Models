import pytorch_lightning as pl
from torchvision.datasets import MNIST
from .base import BaseDatamodule, get_transform


class MNISTDataModule(BaseDatamodule):
    def __init__(
        self,
        data_dir: str = "./data",
        width=64,
        height=64,
        channels=3,
        batch_size: int = 64,
        num_workers: int = 8,
        transforms=None,
        **kargs
    ):
        super().__init__(width, height, channels, batch_size, num_workers)
        self.data_dir = data_dir
        self.transform = get_transform(transforms)

    def prepare_data(self):
        # download
        MNIST(self.data_dir, train=True, download=True)
        MNIST(self.data_dir, train=False, download=True)

    def setup(self, stage=None):
        # Assign train/val datasets for use in dataloaders
        self.train_data = MNIST(self.data_dir, train=True, transform=self.transform)
        self.val_data = MNIST(self.data_dir, train=False, transform=self.transform)