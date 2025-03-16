import os
import numpy as np
import shutil
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

def main():
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

	# Define image transformations
	transform = transforms.Compose([
		transforms.ToTensor(),
		transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
	])

	# Directory containing the logo images
	image_folder = 'logos_resized'
	features = []
	image_paths = []

	# Extract features from each image
	for filename in os.listdir(image_folder):
		if filename.lower().endswith('.png'):
			image_path = os.path.join(image_folder, filename)
			feature_vector = extract_features(image_path, model, transform, device)
			features.append(feature_vector)
			image_paths.append(image_path)

	# Normalize the feature vectors
	features = np.array(features)
	scaler = StandardScaler()
	features_normalized = scaler.fit_transform(features)

	# Apply DBSCAN clustering
	dbscan = DBSCAN(eps=5, min_samples=1, metric='euclidean')
	labels = dbscan.fit_predict(features_normalized)

	# Group images by cluster labels and copy them to respective folders
	clusters = {}
	output_base_folder = 'clustered_logos'
	os.makedirs(output_base_folder, exist_ok=True)

	for label, image_path in zip(labels, image_paths):
		if label != -1:  # Ignore noise points
			if label not in clusters:
				clusters[label] = []
			clusters[label].append(image_path)

	for cluster_id, image_list in clusters.items():
		if image_list:
			# Use the first image's filename as the folder name
			first_image_name = os.path.splitext(os.path.basename(image_list[0]))[0]
			cluster_folder = os.path.join(output_base_folder, first_image_name.split(".")[0])
			os.makedirs(cluster_folder, exist_ok=True)
			for img_path in image_list:
				shutil.copy(img_path, cluster_folder)

	# Write the clustering results to a file
	with open('duplicate_logos.txt', 'w') as f:
		for cluster_id, image_list in clusters.items():
			f.write(f"Cluster {cluster_id}:\n")
			for img_path in image_list:
				f.write(f" - {img_path}\n")
			f.write("\n")

	print(f"Clustering results have been written to 'duplicate_logos.txt'.")
	print(f"Clustered images have been copied to the '{output_base_folder}' directory.")

if __name__ == "__main__":
	main()
