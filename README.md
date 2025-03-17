# LogoSimilarity

### Using an algorithm like this you can detect which domains belong to the same company due to the unique company logo

- First of all, we need to get logos from our domains. To do this, I make GET requests to the domain and search for img tags in the HTML. Then I search for the 
'logo' sequence in the src attribute (or alt) of the img tag. If I find it, I download the image and save it in the logos folder. With this approach, 
I successfully downloaded 3026 logos from 3416 domains (3416 domains without duplicates - df.drop_duplicates()). Most of the failed downloads occur because the 
domains are not  reachable (404 error).  
To make this process faster, I used a ThreadPoolExecutor with 16 workers, allowing multiple logos to be downloaded at the same time.

- After downloading, I need to convert all of them to a single format, so I resized all images to 224x224 pixels and saved them as .png files (I can easily 
visualize them directly in the file explorer). The size is chosen for future use with ResNet18 from PyTorch. Using this approach, I successfully processed 2926 
out of 3026 logos (most of the remaining logos are in a wrong or unusual format).

Now that I have all logos in a single format, I can start with the similarity search. I tried many methods, but I got the best results with two of them:

1. **Extracting features as RGBA values and using DBSCAN (unsupervised learning) with the Euclidean metric for clustering.**  
   `dublicate_logos.txt` contains the results of this approach (I got 1102 clusters). This approach is acceptable as it doesn't mix logos from different domains, but it is not perfect; sometimes it doesn't recognize logos from the same domain and adds them to a separate cluster.

2. **Using ResNet18 from PyTorch to extract features.**  
   (This pretrained model is trained to detect features or forms in images.) I used this model to extract features from the logos and then applied the same DBSCAN 
   algorithm to cluster them. (I also tried the cosine metric, but the results weren't better.)  
   `dublicate_logos_resnet.txt` contains the results of this approach (I got 1189 clusters). This approach also has a problem; for example, cluster 25 contains 
   logos from different domains because they are similar (dark colors and simple similar forms).

**Bonus:** I also tried, when selecting features for clustering, not to use the image but the domain names (for example, the first 3-5 characters). The results 
were good, but I think the task was to find similar logos, not similar domains; besides, this could be done without an ML or neural network algorithm.

To run the code, you need to insert the Parquet file name, as well as the folders to save logos and clustering results, in `main.py` and then run it. In my case, 
I have the results from using the first approach in the `clusterd_logos` folder, which makes it easier to visualize the results.
