# coding=utf-8
import model_train
from torchvision import models

if __name__ == '__main__':
    # train_path = '../Data/car_finemap_detect/car_plate_train'
    # test_path = '../Data/car_finemap_detect/car_plate_test'
    train_path = '../Data/car_finemap_detect_new/car_plate_train'
    test_path = '../Data/car_finemap_detect_new/car_plate_test'

    FILE_PATH = './Model/resnet18_params.pkl'
    model = models.resnet18(num_classes=8)
    model_train = model_train.ModuleTrain(train_path, test_path, FILE_PATH, model=model, batch_size=32, img_size=224, lr=1e-3)

    model_train.train(200, 60)
    # model_train.test(show_img=True)
