import torch
from torch import nn
import torch.distributions as D
import torch.nn.functional as F

def get_decode_dist(name):
    if name == "gaussian":
        return GaussianDistribution()
    elif name == "bernoulli":
        return BernoulliDistribution()
    else:
        raise NotImplementedError

class GaussianDistribution(nn.Module):
    def __init__(self):
        super().__init__()

    def prob(self, pred, target):
        dist = D.Normal(pred, torch.ones_like(pred))
        p_x = dist.log_prob(target).sum(dim=[1,2,3])
        return p_x

    def sample(self, pred):
        return pred

class BernoulliDistribution(nn.Module):
    def __init__(self):
        super().__init__()
    
    def prob(self, pred, target):
        # pred: probabilities between 0 and 1
        prob = -F.binary_cross_entropy(pred, target, reduction='none').sum([1, 2, 3])
        return prob

    def sample(self, pred):
        return torch.bernoulli(pred)
