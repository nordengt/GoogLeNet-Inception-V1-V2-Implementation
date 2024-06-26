import argparse

import torch
from torch import nn
import torch.nn.functional as F

from tqdm import tqdm

from model import GoogLeNet
from dataloader import dataloader
from utils import plot_loss_accuracy, calculate_accuracy

def main(epochs: int, version: int):
    model = None
    if version == 1: model = GoogLeNet() 
    elif version == 2: model = GoogLeNet(bnorm=True) 
    else: raise ValueError("Version 1 and 2 is supported")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    lr = 1e-2
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=0.0005)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=8, gamma=0.04)
    loss_fn = nn.CrossEntropyLoss()

    train_dataloader, test_dataloader = dataloader()

    train_losses, train_accuracies = [], []
    test_losses, test_accuracies = [], []

    model.to(device)
    
    for epoch in tqdm(range(epochs)):
        train_loss, train_acc = 0, 0
        model.train()
        for X, y in train_dataloader:
            X, y = X.to(device), y.to(device)
            y_pred, y_aux4d, y_aux4a = model(X)
            loss = loss_fn(y_pred, y) + loss_fn(y_aux4d, y)*0.3 + loss_fn(y_aux4a, y)*0.3
            train_loss += loss.item()
            train_acc += calculate_accuracy(F.softmax(y_pred, dim=1), y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        scheduler.step()
        
        if epoch % 10 == 0:
            test_loss, test_acc = 0, 0
            model.eval()
            with torch.inference_mode():
                for X, y in test_dataloader:
                    X, y = X.to(device), y.to(device)
                    y_pred, y_aux4d, y_aux4a = model(X)
                    loss = loss_fn(y_pred, y) + loss_fn(y_aux4d, y)*0.3 + loss_fn(y_aux4a, y)*0.3
                    test_acc += calculate_accuracy(F.softmax(y_pred, dim=1), y)
                    test_loss += loss.item()
            
            train_loss /= len(train_dataloader)
            test_loss /= len(test_dataloader)
            train_acc /= len(train_dataloader)
            test_acc /= len(test_dataloader)

            train_losses.append(train_loss)
            test_losses.append(test_loss)
            train_accuracies.append(train_acc)
            test_accuracies.append(test_acc)
            
            print(f"Epoch: {epoch} | Train Loss: {train_loss:.2f} Train Accuracy: {train_acc*100:.2f} | Test Loss: {test_loss:.2f} Test Accuracy: {test_acc*100:.2f}")
    
    plot_loss_accuracy(train_losses, test_losses, train_accuracies, test_accuracies, save=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Script")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args()
    main(args.epochs, args.version)