import os
import shutil
from get_clusters import dbscan_with_resnet18, dbscan
from extract_logos import extract_logos
from prepare_logos import prepare_logos

def delete_folder(folder):
	if os.path.exists(folder):
		shutil.rmtree(folder)

def main():
	# if they are already downloaded, you can skip this step
	extract_logos(parquet="logos.snappy.parquet", folder="logos")
	prepare_logos("logos", "logos_resized")

	image_paths = []
	labels = dbscan(image_paths, 'logos_resized')
	# labels = dbscan_with_resnet18(image_paths, 'logos_resized')

	clusters = {}
	output_base_folder = 'clustered_logos'
	output_txt_file = 'duplicate_logos.txt'
	delete_folder(output_base_folder)
	os.makedirs(output_base_folder, exist_ok=True)

	for label, image_path in zip(labels, image_paths):
		if label != -1:
			clusters.setdefault(label, []).append(image_path)

	for cluster_id, image_list in clusters.items():
		if image_list:
			# Use the first image name as the cluster folder name
			first_image_name = os.path.splitext(os.path.basename(image_list[0]))[0]
			cluster_folder = os.path.join(output_base_folder, first_image_name.split(".")[0])
			os.makedirs(cluster_folder, exist_ok=True)
			for img_path in image_list:
				shutil.copy(img_path, cluster_folder)

	with open(output_txt_file, 'w') as f:
		for cluster_id, image_list in clusters.items():
			f.write(f"Cluster {cluster_id}:\n")
			for img_path in image_list:
				f.write(f" - {img_path}\n")
			f.write("\n")
			
	with open(output_txt_file, 'r') as f:
		print(f.read())

	print("Rezultatele clusteringului au fost scrise în 'duplicate_logos.txt'.")
	print(f"Imaginile clusterizate au fost copiate în directorul '{output_base_folder}'.")

if __name__ == "__main__":
	main()
