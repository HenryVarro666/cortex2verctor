import math
import numpy
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module

from Graph_embedding_loss import mse
import pdb


class graph_embedding(nn.Module):
    def __init__(self, embedding_num, embedding_dim, hot_num):
        super(graph_embedding, self).__init__()

        self.w_node_embedding = nn.Linear(embedding_num, embedding_dim)
        self.embedding_combine_coef = nn.Linear(hot_num, 1)
        self.decoder_divide_coef = nn.Linear(1, hot_num)
        self.w_node_decoder = nn.Linear(embedding_dim, embedding_num)

    def forward(self, multi_hot_feature):
        # pdb.set_trace()
        x_embedding = self.w_node_embedding(multi_hot_feature)
        x_combine = self.embedding_combine_coef(x_embedding.permute(0, 2, 1))
        x_de_embedding = self.decoder_divide_coef(x_combine)
        x_de_embedding = x_de_embedding.permute(0, 2, 1)
        x_decoder = self.w_node_decoder(x_de_embedding)
        return x_decoder, x_embedding, x_de_embedding, x_combine.permute(0, 2, 1)


class graph_embedding2(nn.Module):
    def __init__(self, embedding_num, embedding_dim, hot_num):
        super(graph_embedding2, self).__init__()

        self.w_node_embedding = nn.Linear(embedding_num, embedding_dim, bias=False)
        torch.nn.init.eye_(self.w_node_embedding.weight)
        self.embedding_combine_coef = nn.Linear(hot_num, 1)
        self.decoder_divide_coef = nn.Linear(1, hot_num)
        self.w_node_decoder = nn.Linear(embedding_dim, embedding_num)

    def forward(self, multi_hot_feature):
        # pdb.set_trace()
        x_embedding = self.w_node_embedding(multi_hot_feature)
        x_embedding = F.leaky_relu(x_embedding, 0.1, inplace=True)
        x_combine = self.embedding_combine_coef(x_embedding.permute(0, 2, 1))
        x_de_embedding = self.decoder_divide_coef(x_combine)
        x_de_embedding = x_de_embedding.permute(0, 2, 1)
        x_de_embedding = F.leaky_relu(x_de_embedding, 0.1, inplace=True)
        x_decoder = self.w_node_decoder(x_de_embedding)
        return x_decoder, x_embedding, x_de_embedding, x_combine.permute(0, 2, 1)


if __name__ == '__main__':
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    cuda = True if torch.cuda.is_available() else False

    batchSize = 64
    hot_num = 4
    embedding_num = 75
    embedding_dim = 128
    multi_hot_feature = torch.rand(batchSize, hot_num, embedding_num).to(device).float()
    model = graph_embedding(embedding_num, embedding_dim, hot_num)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005, betas=(0.5, 0.999))

    Tensor = torch.cuda.FloatTensor if cuda else torch.FloatTensor

    for epoch in range(1000):
        optimizer.zero_grad()

        x_decoder, x_embedding, x_de_embedding, x_combine = model(multi_hot_feature)
        loss = mse(multi_hot_feature, x_decoder, hot_num) + mse(x_embedding, x_de_embedding, hot_num)
        print('epoch-----:', epoch, 'generator_loss:', loss)

        loss.backward()
        optimizer.step()