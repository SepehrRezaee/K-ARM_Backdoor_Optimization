# K-Arm Optimization
########################################################################################################################################
### K_Arm_Opt functions load data based on different trigger types, then create an instance of K-Arm scanner and run optimization    ###
### It returns the target-victim pair and corresponding pattern, mask and l1 norm of the mask                                        ###
########################################################################################################################################

import torch 
from torchvision import transforms

import sys

sys.path.append('/kaggle/working/K-ARM_Backdoor_Optimization')

import random

from dataset import CustomDataSet
from torch.utils.data import DataLoader
import torch.nn.functional as F
import numpy as np
from K_Arm_Scanner import *

import pandas as pd



def K_Arm_Opt(args,target_classes_all,triggered_classes_all,trigger_type,model,direction):

    df = pd.read_csv("/kaggle/working/examples_2/data.csv")
    target_class_all1 = df["target_labe"]
    triggered_classes_all1 = df[df["trigger"] == True]["true_label"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    transform = transforms.Compose([
        transforms.CenterCrop(args.input_width),
        transforms.ToTensor()
        ])

    data_loader_arr = []
    if triggered_classes_all is None:

        data_set = CustomDataSet(args.examples_dirpath,transform=transform,triggered_classes=triggered_classes_all)
        data_loader = DataLoader(dataset=data_set,batch_size = args.batch_size,shuffle=False,drop_last=False,num_workers=8,pin_memory=True)
        data_loader_arr.append(data_loader)
        print("triggered_classes_all is None")
    
    else:
        for i in range(len(target_classes_all)):
            data_set = CustomDataSet(args.examples_dirpath,transform=transform,triggered_classes=triggered_classes_all[i],label_specific=True)
            data_loader = DataLoader(dataset=data_set,batch_size = args.batch_size,shuffle=False,drop_last=False,num_workers=8,pin_memory=True)
            data_loader_arr.append(data_loader)


    k_arm_scanner = K_Arm_Scanner(model,args)


    if args.single_color_opt == True and trigger_type == 'polygon_specific':
        pattern = torch.rand(1,args.channels,1,1).to(device)
    
    else:
        pattern = torch.rand(1,args.channels,args.input_width,args.input_height).to(device)
        #only for r1
        #pattern = torch.rand(1,args.channels,1,1).to(device)
    pattern = torch.clamp(pattern,min=0,max=1)



    #K-arms Bandits
    if trigger_type == 'polygon_global':
        #args.early_stop_patience = 5

        mask = torch.rand(1,args.input_width,args.input_height).to(device)
        

    elif trigger_type == 'polygon_specific':

        if args.central_init:
            mask = torch.rand(1,args.input_width,args.input_height).to(device) * 0.001
            mask[:,112-25:112+25,112-25:112+25] = 0.99
        
        else:
            mask = torch.rand(1,args.input_width,args.input_height).to(device)

    
    mask = torch.clamp(mask,min=0,max=1)

    if args.num_classes == 1:
        start_label_index = 0
    else:
        #start_label_index = torch.randint(0,args.num_classes-1,(1,))[0].item()
        start_label_index = 0

    pattern, mask, l1_norm, total_times = k_arm_scanner.scanning(target_classes_all,data_loader_arr,start_label_index,pattern,mask,trigger_type,direction)
    # index = torch.argmin(torch.Tensor(l1_norm))
    if l1_norm:
        
        index = torch.argmin(torch.Tensor(l1_norm)).item()
        target_class = target_classes_all[index]
    else:
        
        print("Error: l1_norm is empty. Cannot determine target class.")
        
        index = None
        target_class = None


    '''
    print(pattern[index]) 
    print(mask[index])
    print(total_times[index])
    '''
    index = random.randint(0, len(target_class_all1))
    print("index:", index)
    if triggered_classes_all is None:
        target_class =  target_classes_all[index]
        triggered_class = 'all'

    else:
        
        target_class = target_classes_all[index]
        triggered_class = triggered_classes_all[index]



    return l1_norm[index], mask[index],target_class,triggered_class,total_times[index]


# def K_Arm_Opt(args, target_classes_all, triggered_classes_all, trigger_type, model, direction):
#     # Check if there are any target classes provided
#     if not target_classes_all:
#         print("Error: target_classes_all is empty. No classes to target.")
#         return None, None, None, None, None

#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     transform = transforms.Compose([
#         transforms.CenterCrop(args.input_width),
#         transforms.ToTensor()
#     ])

#     data_loader_arr = []
#     if triggered_classes_all is None:
#         data_set = CustomDataSet(args.examples_dirpath, transform=transform, triggered_classes=triggered_classes_all)
#         data_loader = DataLoader(dataset=data_set, batch_size=args.batch_size, shuffle=False, drop_last=False, num_workers=8, pin_memory=True)
#         data_loader_arr.append(data_loader)
#     else:
#         for i in range(len(target_classes_all)):
#             data_set = CustomDataSet(args.examples_dirpath, transform=transform, triggered_classes=triggered_classes_all[i], label_specific=True)
#             data_loader = DataLoader(dataset=data_set, batch_size=args.batch_size, shuffle=False, drop_last=False, num_workers=8, pin_memory=True)
#             data_loader_arr.append(data_loader)

#     k_arm_scanner = K_Arm_Scanner(model, args)

#     if args.single_color_opt == True and trigger_type == 'polygon_specific':
#         pattern = torch.rand(1, args.channels, 1, 1).to(device)
#     else:
#         pattern = torch.rand(1, args.channels, args.input_width, args.input_height).to(device)

#     pattern = torch.clamp(pattern, min=0, max=1)

#     if trigger_type == 'polygon_global':
#         mask = torch.rand(1, args.input_width, args.input_height).to(device)
#     elif trigger_type == 'polygon_specific':
#         if args.central_init:
#             mask = torch.rand(1, args.input_width, args.input_height).to(device) * 0.001
#             mask[:, 112-25:112+25, 112-25:112+25] = 0.99
#         else:
#             mask = torch.rand(1, args.input_width, args.input_height).to(device)

#     mask = torch.clamp(mask, min=0, max=1)

#     start_label_index = 0
#     pattern, mask, l1_norm, total_times = k_arm_scanner.scanning(target_classes_all, data_loader_arr, start_label_index, pattern, mask, trigger_type, direction)

#     if not l1_norm:
#         print("Error: l1_norm is empty. Cannot determine target class.")
#         return None, None, None, None, None

#     index = torch.argmin(torch.Tensor(l1_norm)).item()
#     target_class = target_classes_all[index]

#     if triggered_classes_all is None:
#         triggered_class = 'all'
#     else:
#         triggered_class = triggered_classes_all[index]

#     return l1_norm[index], mask[index], target_class, triggered_class, total_times[index]
