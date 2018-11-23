# encoding:utf-8
import os
import random
import numpy as np
from PIL import Image
from torch.autograd import Function
import torch
import torch.nn.functional as F
import torch.optim as optim
from torchvision import transforms as T
from torchvision.datasets import ImageFolder
from torchvision.transforms import functional
from torch.autograd import Variable
from torch.utils.data import DataLoader
import cv2


class ModuleTrain:
    def __init__(self, train_path, test_path, model_file, model, img_size=178, batch_size=8, lr=1e-3,
                 re_train=False, best_loss=0.3):
        self.train_path = train_path
        self.test_path = test_path
        self.model_file = model_file
        self.img_size = img_size
        self.batch_size = batch_size
        self.re_train = re_train                        # 不加载训练模型，重新进行训练
        self.best_loss = best_loss                      # 最好的损失值，小于这个值，才会保存模型

        if torch.cuda.is_available():
            self.use_gpu = True
        else:
            self.use_gpu = False

        # 模型
        self.model = model

        if self.use_gpu:
            print('[use gpu] ...')
            self.model = self.model.cuda()

        # 加载模型
        if os.path.exists(self.model_file) and not self.re_train:
            self.load(self.model_file)

        # RandomHorizontalFlip
        self.transform_train = T.Compose([
            T.Resize((self.img_size, self.img_size)),
            T.ToTensor(),
            T.Normalize(mean=[.5, .5, .5], std=[.5, .5, .5]),
        ])

        self.transform_test = T.Compose([
            T.Resize((self.img_size, self.img_size)),
            T.ToTensor(),
            T.Normalize(mean=[.5, .5, .5], std=[.5, .5, .5])
        ])

        # Dataset
        # train_label = os.path.join(self.train_path, 'label.txt')
        # train_dataset = MyDataset(self.train_path, train_label, self.img_size, self.transform_test, is_train=True)
        # test_label = os.path.join(self.test_path, 'label.txt')
        # test_dataset = MyDataset(self.test_path, test_label, self.img_size, self.transform_test, is_train=False)
        train_dataset = ImageFolder(root=self.train_path, transform=self.transform_train)
        test_dataset = ImageFolder(root=self.test_path, transform=self.transform_test)

        # Data Loader (Input Pipeline)
        self.train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
        self.test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

        # self.loss = F.mse_loss
        # self.loss = F.smooth_l1_loss
        self.loss = F.cross_entropy

        self.lr = lr
        # self.optimizer = optim.SGD(self.model.parameters(), lr=self.lr, momentum=0.5)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.lr)

        pass

    def train(self, epoch, decay_epoch=40, save_best=True):
        print('[train] epoch: %d' % epoch)
        for epoch_i in range(epoch):

            if epoch_i >= decay_epoch and epoch_i % decay_epoch == 0:                   # 减小学习速率
                self.lr = self.lr * 0.1
                self.optimizer = optim.Adam(self.model.parameters(), lr=self.lr)

            print('================================================')
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = Variable(data), Variable(target)

                if self.use_gpu:
                    data = data.cuda()
                    target = target.cuda()

                # 梯度清0
                self.optimizer.zero_grad()

                # 计算损失
                output = self.model(data)
                loss = self.loss(output, target)

                # 反向传播计算梯度
                loss.backward()

                # 更新参数
                self.optimizer.step()

                # update
                if batch_idx == 0:
                    print('[Train] Epoch: {} [{}/{}]\tLoss: {:.6f}\tlr: {}'.format(epoch_i, batch_idx * len(data),
                        len(self.train_loader.dataset), loss.item()/self.batch_size, self.lr))

            test_loss = self.test()
            if save_best is True:
                if self.best_loss > test_loss:
                    self.best_loss = test_loss
                    str_list = self.model_file.split('.')
                    best_model_file = ""
                    for str_index in range(len(str_list)):
                        best_model_file = best_model_file + str_list[str_index]
                        if str_index == (len(str_list) - 2):
                            best_model_file += '_best'
                        if str_index != (len(str_list) - 1):
                            best_model_file += '.'
                    self.save(best_model_file)                                  # 保存最好的模型

        self.save(self.model_file)

    def test(self, show_img=False):
        test_loss = 0
        correct = 0

        # 测试集
        for data, target in self.test_loader:
            # print('[test] data.size: ', data.size())
            data, target = Variable(data), Variable(target)
            # print('[test] data.size: ', data.size())

            if self.use_gpu:
                data = data.cuda()
                target = target.cuda()

            output = self.model(data)
            # sum up batch loss
            if self.use_gpu:
                loss = self.loss(output, target)
            else:
                loss = self.loss(output, target)
            test_loss += loss.item()

        test_loss /= len(self.test_loader.dataset)
        print('[Test] set: Average loss: {:.4f}\n'.format(test_loss))
        return test_loss

    def load(self, name):
        print('[Load model] %s ...' % name)
        self.model.load_state_dict(torch.load(name))
        # self.model.load(name)

    def save(self, name):
        print('[Save model] %s ...' % name)
        torch.save(self.model.state_dict(), name)
        # self.model.save(name)

    def show_img(self, img_file, output, target):
        # print(img_file)
        # print(output)
        # print(target)

        img = cv2.imread(img_file)
        h, w, c = img.shape
        for i in range(len(target)/2):
            cv2.circle(img, (int(target[2*i]*h/self.img_size), int(target[2*i+1]*h/self.img_size)), 3, (0, 255, 0), -1)

        for i in range(len(output)/2):
            cv2.circle(img, (int(output[2*i]*h/self.img_size), int(output[2*i+1]*h/self.img_size)), 3, (0, 0, 255), -1)

        cv2.imshow('show_img_1', img)
        cv2.waitKey(0)