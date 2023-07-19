import os, glob
import torch, sys
from torch.utils.data import Dataset
from .data_utils import pkload
import matplotlib.pyplot as plt
import random
import numpy as np
import nibabel as nib


class OASIS3BrainDataset(Dataset):
    def __init__(self, data_path, transforms, max_dataset_size):
        file_list = os.listdir(data_path)
        self.paths = [os.path.join(data_path, file) for file in file_list]
        self.transforms = transforms
        self.max_dataset_size = max_dataset_size

    def one_hot(self, img, C):
        out = np.zeros((C, img.shape[1], img.shape[2], img.shape[3]))
        for i in range(C):
            out[i,...] = img == i
        return out

    def __getitem__(self, index):
        path = self.paths[index]
        tar_list = self.paths.copy()
        tar_list.remove(path)
        random.shuffle(tar_list)
        tar_file = tar_list[0]
        x = nib.load(os.path.join(os.path.join(path, 'T1w'), 'orig_nu_noskull.nii.gz'))
        y = nib.load(os.path.join(os.path.join(tar_file, 'T1w'), 'orig_nu_noskull.nii.gz'))
        # Get data array from NIfTI
        x, y = x.get_fdata(), y.get_fdata()

        x = self.transforms([x])
        y = self.transforms([y])
        x = np.ascontiguousarray(x)  
        y = np.ascontiguousarray(y)

        # Add extra dim to x and y (128, 128, 128) -> (1, 128, 128, 128)
        # [Bsize,channels,Height,Width,Depth]
        x, y = x[None, ...], y[None, ...]
        x, y = torch.from_numpy(x), torch.from_numpy(y)
        return x, y, os.path.basename(os.path.normpath(path)), os.path.basename(os.path.normpath(tar_file))

    def __len__(self):
        return min(len(self.paths), self.max_dataset_size)


class OASISBrainInferDataset(Dataset):
    def __init__(self, data_path, transforms, max_dataset_size, seg_transforms=None):
        file_list = os.listdir(data_path)
        self.paths = [os.path.join(data_path, file) for file in file_list]
        self.transforms = transforms
        self.max_dataset_size = max_dataset_size
        self.seg_path = '/SauronExt4/MedicalImaging/NeuroImages/Synth_segs/segs'
        self.seg_transforms = seg_transforms

    def one_hot(self, img, C):
        out = np.zeros((C, img.shape[1], img.shape[2], img.shape[3]))
        for i in range(C):
            out[i,...] = img == i
        return out

    def __getitem__(self, index):
        path = self.paths[index]
        tar_list = self.paths.copy()
        tar_list.remove(path)
        random.shuffle(tar_list)
        tar_file = tar_list[0]
        x = nib.load(os.path.join(os.path.join(path, 'T1w'), 'orig_nu_noskull.nii.gz'))
        y = nib.load(os.path.join(os.path.join(tar_file, 'T1w'), 'orig_nu_noskull.nii.gz'))
        # Get data array from NIfTI
        x, y = x.get_fdata(), y.get_fdata()
        x = self.transforms([x])
        y = self.transforms([y])
        x = np.ascontiguousarray(x)  # [Bsize,channels,Height,Width,Depth]
        y = np.ascontiguousarray(y)
        # Add extra dim to x and y (256, 256, 256) -> (1, 256, 256, 256)
        x, y = x[None, ...], y[None, ...]
        x, y = torch.from_numpy(x), torch.from_numpy(y)

        # Load segmentations
        path_seg = os.path.basename(os.path.normpath(path)) + '_synthseg.nii.gz'
        tar_file_seg = os.path.basename(os.path.normpath(tar_file))  + '_synthseg.nii.gz'

        x_seg = nib.load(os.path.join(self.seg_path, path_seg))
        y_seg = nib.load(os.path.join(self.seg_path, tar_file_seg))
        # Get data array from NIfTI
        x_seg, y_seg = x_seg.get_fdata(), y_seg.get_fdata()
        x_seg = x_seg.astype(np.int16)
        y_seg = y_seg.astype(np.int16)

        if self.seg_transforms != None:
            x_seg = self.seg_transforms([x_seg])
            y_seg = self.seg_transforms([y_seg])
            
        x_seg = np.ascontiguousarray(x_seg)
        y_seg = np.ascontiguousarray(y_seg)
        # Add extra dim to x and y (256, 256, 256) -> (1, 256, 256, 256)
        x_seg, y_seg = x_seg[None, ...], y_seg[None, ...]
        x_seg, y_seg = torch.from_numpy(x_seg), torch.from_numpy(y_seg)
        return x, y, x_seg, y_seg

    def __len__(self):
        return min(len(self.paths), self.max_dataset_size)