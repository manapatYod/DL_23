#-----------------------------------------------------------------------------------------#
import sys
sys.path.append('./Libs') 
import utilities as U
import neural_network_architectures as NNA
#-----------------------------------------------------------------------------------------#
import torch
import torch.nn as nn
import torch.utils.data as data
import torch.optim as optim
import time
#-----------------------------------------------------------------------------------------#
from torchvision import datasets, transforms
from torchsummary import summary
#-----------------------------------------------------------------------------------------#
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using PyTorch version:', torch.__version__, ' Device:', device)
#-----------------------------------------------------------------------------------------#

# NOTE predifined parameters
download_folder = '../datasets/'
batch_size = 128 # depends on GPU memory size
image2plot = 25
val_ratio = 0.8
image_dim_1 = 32; image_dim_2 = 32
output_dim = 10 # should equal to number of classes
learning_rate = 0.01
momentum = 0.5
epochs = 10
save_model = '../save_trained_model/AlexNet.pt'

'''
step 1: load CIFAR10.
'''

train_data = datasets.CIFAR10(root=download_folder,
                              train=True,
                              download=True)

'''
step 2: normalize data.
'''

# NOTE compute mean and standard diviation.
means = train_data.data.mean(axis=(0, 1, 2)) / 255
stds = train_data.data.std(axis=(0, 1, 2)) / 255
print(f'Calculated means: {means}')
print(f'Calculated stds: {stds}')
# NOTE transform to PyTorch format
train_transforms = transforms.Compose([transforms.ToTensor(),
                                      transforms.Normalize(mean=means, std=stds)])
test_transforms = transforms.Compose([transforms.ToTensor(),
                                     transforms.Normalize(mean=means, std=stds)])
train_data = datasets.CIFAR10(download_folder,
                              train=True,
                              download=True,
                              transform=train_transforms)
test_data = datasets.CIFAR10(download_folder,
                             train=False,
                             download=True,
                             transform=test_transforms)
# NOTE store class names for plotting
classes = train_data.classes
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
# NOTE preview some images
# images, labels = zip(*[(image, label) for image, label in
#                        [train_data[i] for i in range(image2plot)]])
# NOTE image without appling normalization
# U.plot_CIFAR10(images, labels, classes)
# NOTE image with appling normalization
# U.plot_CIFAR10(images, labels, classes, normalize=True)

'''
step 3: divide some parts of the training data for validation. Remember that validation data should be separated from training data. This data set will be used for optimization purposes, whereas test data (unseen data) will be used for evaluating model performance.
'''

# NOTE devide some parts of the training data for validation
n_train_examples = int(len(train_data) * val_ratio)
n_valid_examples = len(train_data) - n_train_examples
# NOTE random split
train_data, valid_data = data.random_split(train_data, [n_train_examples, n_valid_examples])
print(f'Number of training examples: {len(train_data)}')
print(f'Number of validation examples: {len(valid_data)}')
print(f'Number of testing examples: {len(test_data)}')
# NOTE preview some images
# images, labels = zip(*[(image, label) for image, label in
#                        [valid_data[i] for i in range(image2plot)]])
# U.plot_CIFAR10(images, labels, classes, normalize=True)

'''
step 4: split training, validation, and test data to fit GPU/CPU. This technique helps parallel computation. The size of the splitting depends on the cores in GPU/CPU.
'''

train_iterator = data.DataLoader(train_data, shuffle=True, batch_size=batch_size)
valid_iterator = data.DataLoader(valid_data, batch_size=batch_size)
test_iterator = data.DataLoader(test_data, batch_size=batch_size)

'''
step 5: verify neural network architecture. 
'''

model = NNA.AlexNet(output_dim)
print(model.to(device))
summary(model, (3, image_dim_1, image_dim_2))
optimizer = optim.Adam(model.parameters())
criterion = nn.CrossEntropyLoss()
model = model.to(device)
criterion = criterion.to(device)

'''
step 6: train and validate neural network architecture. Remember, we need to create a folder to store the trained model.
'''

best_valid_loss = float('inf')
for epoch in range(epochs):
    start_time = time.monotonic()
    train_loss, train_acc = U.train(model, train_iterator, optimizer, criterion, device)
    valid_loss, valid_acc = U.evaluate(model, valid_iterator, criterion, device)
    if valid_loss < best_valid_loss:
        best_valid_loss = valid_loss
        torch.save(model.state_dict(), save_model)
    end_time = time.monotonic()
    epoch_mins, epoch_secs = U.epoch_time(start_time, end_time)
    print(f'Epoch: {epoch+1:02} | Epoch Time: {epoch_mins}m {epoch_secs}s')
    print(f'\tTrain Loss: {train_loss:.3f} | Train Acc: {train_acc*100:.2f}%')
    print(f'\t Val. Loss: {valid_loss:.3f} |  Val. Acc: {valid_acc*100:.2f}%')

'''
step 7: load the trained model and evaluate it, using confusion matrix.
'''

model.load_state_dict(torch.load(save_model))
test_loss, test_acc = U.evaluate(model, test_iterator, criterion, device)
print(f'Test Loss: {test_loss:.3f} | Test Acc: {test_acc*100:.2f}%')
images, labels, probs = U.get_predictions(model, test_iterator, device)
pred_labels = torch.argmax(probs, 1)
U.plot_confusion_matrix_CIFAR10(labels, pred_labels, classes)

'''
step 8: display the most incorrect predictions based on probabilities.
'''

corrects = torch.eq(labels, pred_labels)
incorrect_examples = []
for image, label, prob, correct in zip(images, labels, probs, corrects):
    if not correct:
        incorrect_examples.append((image, label, prob))
incorrect_examples.sort(reverse = True, key=lambda x: torch.max(x[2], dim=0).values)
U.plot_most_incorrect_CIFAR10(incorrect_examples, classes, image2plot)