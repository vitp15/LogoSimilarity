import os
import numpy as np
from PIL import Image
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import torch
import torchvision.models as models
import torchvision.transforms as transforms

def extract_features(image_path, model, transform, device):
	"""Extract feature vector from an image using a pre-trained CNN."""
	image = Image.open(image_path).convert('RGB')
	image = transform(image).unsqueeze(0).to(device)
	with torch.no_grad():
		features = model(image)
	return features.cpu().numpy().flatten()

def extract_features_rgba(image_path, size=(64, 64)):
	"""
	Extrage vectorul de trăsături dintr-o imagine PNG folosind valorile RGBA.
	Se redimensionează imaginea la o dimensiune fixă pentru a asigura o lungime constantă a vectorului.
	"""
	image = Image.open(image_path).convert('RGBA')
	image = image.resize(size)
	image_array = np.array(image)
	feature_vector = image_array.flatten()
	return feature_vector

def extract_features_filename(image_path):
	"""
	Extrage vectorul de trăsături dintr-un nume de fișier.
	Se extrag caracterele numerice din numele fișierului și se normalizează la [0, 1].
	"""
	feature_vector = [ord(c) for c in os.path.basename(image_path)[:4]]
	return feature_vector


def dbscan_with_resnet18(image_paths: list, path: str = 'logos_resized'):
	# Set device to GPU if available, otherwise CPU
	device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

	# Load pre-trained ResNet18 model and remove the classification layer
	if not os.path.exists('resnet18.pth'):
		model = models.resnet18(pretrained=True)
		model = torch.nn.Sequential(*(list(model.children())[:-1]))  # Remove the classification layer
		model = model.to(device).eval()
		torch.save(model.state_dict(), 'resnet18.pth')
	else:
		model = models.resnet18()
		model = torch.nn.Sequential(*(list(model.children())[:-1]))  # Remove the classification layer
		model.load_state_dict(torch.load('resnet18.pth', map_location=device))
		model = model.to(device).eval()

	transform = transforms.Compose([
		transforms.ToTensor(),
		transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
	])

	image_folder = path
	features = []

	# Extract features from each image
	for filename in os.listdir(image_folder):
		if filename.lower().endswith('.png'):
			image_path = os.path.join(image_folder, filename)
			feature_vector = extract_features(image_path, model, transform, device)
			features.append(feature_vector)
			image_paths.append(image_path)

	features = np.array(features)
	scaler = StandardScaler()
	features_normalized = scaler.fit_transform(features)

	dbscan = DBSCAN(eps=5, min_samples=1, metric='euclidean')
	return dbscan.fit_predict(features_normalized)

def dbscan(image_paths: list, path: str = 'logos_resized'):
	image_folder = path
	features = []

	for filename in os.listdir(image_folder):
		if filename.lower().endswith('.png'):
			image_path = os.path.join(image_folder, filename)
			feature_vector = extract_features_rgba(image_path)
			features.append(feature_vector)
			image_paths.append(image_path)

	features = np.array(features)

	scaler = StandardScaler()
	features_normalized = scaler.fit_transform(features)

	dbscan = DBSCAN(eps=15, min_samples=1, metric='euclidean')
	return dbscan.fit_predict(features_normalized)
