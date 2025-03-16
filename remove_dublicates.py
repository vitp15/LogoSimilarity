import os
from collections import defaultdict

def delete_duplicates_by_prefix(folder):
	groups = defaultdict(list)
	
	for filename in os.listdir(folder):
		file_path = os.path.join(folder, filename)
		if os.path.isfile(file_path):
			prefix = filename.split(".")[0][:4]
			groups[prefix].append(filename)

	for prefix, files in groups.items():
		if len(prefix) == 4 and prefix[:3] in groups:
			groups[prefix[:3]] += files
	
	for prefix, files in groups.items():
		if len(files) > 1:
			file_to_keep = files[0]
			print(f"Keeping file: {file_to_keep} (prefix: {prefix})")
			for filename in files[1:]:
				file_to_delete = os.path.join(folder, filename)
				try:
					os.remove(file_to_delete)
					print(f"Deleted {file_to_delete}")
				except Exception as e:
					print(f"Error deleting {file_to_delete}: {e}")

if __name__ == "__main__":
	folder_path = "logos_resized"
	delete_duplicates_by_prefix(folder_path)
