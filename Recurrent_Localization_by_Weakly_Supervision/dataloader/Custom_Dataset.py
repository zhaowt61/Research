from torch.utils.data import Dataset, DataLoader
import pandas as pd
from PIL import Image
from xml.dom import minidom
from torchvision import transforms
import numpy as np
import torch


class CUB(Dataset):
    def __init__(self, root_dir, train_data, test_data, val_data, mode='train', val_frac=0.002):
        self.mode = mode
        self.root_dir = root_dir

        self.train_data = pd.read_csv(train_data)
        self.val_data = pd.read_csv(val_data)
        self.test_data = pd.read_csv(test_data)

    def __getitem__(self, index):
        if self.mode == 'train':
            item = self.train_data.loc[index]

            img_name = item['img_name']
            img_path = item['path']
            img_label = torch.squeeze(torch.from_numpy(np.array(int(str(item['label']).strip())).reshape(-1)))

            img = Image.open(self.root_dir + 'images/' + img_path).convert('RGB')

            img = image_transform(mode='train')(img)

            return img_name, img, img_label

        elif self.mode == 'val':
            item = self.val_data.loc[index]
            img_name = item['img_name']
            img_path = item['path']
            img_label = torch.squeeze(torch.from_numpy(np.array(int(str(item['label']).strip())).reshape(-1)))
            img = Image.open(self.root_dir + 'images/' + img_path).convert('RGB')
            img = image_transform(mode='val')(img)

            return img_name, img, img_label

        else:
            item = self.test_data.loc[index]
            img_name = item['img_name']
            img_path = item['path']
            img_label = torch.squeeze(torch.from_numpy(np.array(int(str(item['label']).strip())).reshape(-1)))
            img = Image.open(self.root_dir + 'images/' + img_path).convert('RGB')
            img = image_transform(mode='test')(img)

            return img_name, img, img_label

    def __len__(self):
        if self.mode == 'train':
            return len(self.train_data)
        if self.mode == 'val':
            return len(self.val_data)
        if self.mode == 'test':
            return len(self.test_data)


def image_transform(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225], mode='train'):
    img_size = 256
    crop_size = 224
    if mode == 'train':
        horizontal_flip = 0.5
        vertical_flip = 0.5

        t = [
            transforms.Resize((img_size, img_size)),
            transforms.RandomCrop(crop_size),
            transforms.RandomHorizontalFlip(horizontal_flip),
            transforms.RandomVerticalFlip(vertical_flip),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]

    else:
        t = [
            transforms.Resize((img_size, img_size)),
            transforms.RandomCrop(crop_size),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]

    return transforms.Compose([v for v in t])


if __name__ == '__main__':
    CUB()
