from videohash import VideoHash
from pytube import YouTube
import pandas as pd
import numpy as np
import csv
import logging
import os
import itertools

# logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)
# logging.basicConfig(level=logging.ERROR)
# logging.basicConfig(level=logging.CRITICAL)

class VideoSimilarityTester:
    #* Class to test similarity between videos
    def __init__(self, URL_list_filepath: str, cache_path:str, download_resolution=0, export_video_detail=False, export_comparison_result=False, remove_cache=True, similar_percentage=15) -> None:
        #* Load URL list from file
        self.URL_list_filepath = URL_list_filepath
        self.cache_path = cache_path
        self.download_resolution = download_resolution
        self.export_video_detail = export_video_detail
        self.export_comparison_result = export_comparison_result
        self.remove_cache = remove_cache
        self.similar_percentage = similar_percentage
        self.URL_list = np.empty(0, dtype=str)
        self.video_detail_dataframe = pd.DataFrame(columns=["URL", "PATH", "HASH", "HASH_HEX", "COLLAGE_PATH", "BITS_IN_HASH"])
        with open(self.URL_list_filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                self.URL_list = np.append(self.URL_list, row[0])
        self.video_detail_dataframe["URL"] = self.URL_list
        logging.debug("Loaded URL list: {}".format(self.URL_list))
        logging.info("Loaded URL list from {} with {} {} files.".format(self.URL_list_filepath, self.URL_list.shape[0], self.URL_list.shape))
        print("URL list loading phase complete.")
        #* Call next function on the line
        self._download_video()
        self._hash_video()
        self._compare_video()
        self._remove_cache()

    def _download_video(self) -> None:
        #* Download video from URL
        self.PATH_list = np.empty(0, dtype=str)
        for i, url in enumerate(self.URL_list):
            logging.debug("Downloading video from {}.".format(url))
            path = os.path.join(self.cache_path, str(i)+".mp4")
            path = os.path.abspath(path)
            logging.debug("Saving file is: ".format(path))
            #* Download video from URL & Save video to file
            yt = YouTube(url)
            yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first().download(filename=path)
            #* Save data to list
            self.PATH_list = np.append(self.PATH_list, path)
            print("Downloaded {}/{} videos.".format(i+1, self.URL_list.shape[0]), end="\r")
        if self.PATH_list.shape[0] != self.URL_list.shape[0]:
            logging.warning("Some videos are not downloaded.")
        self.video_detail_dataframe["PATH"] = self.PATH_list
        logging.debug("Downloaded video list: {}".format(self.PATH_list))
        logging.info("Downloaded {} videos.".format(self.PATH_list.shape[0]))
        print("Video downloading phase complete.")

    def _hash_video(self) -> None:
        #* Hash video
        self.VideoHash_list = []
        self.HASH_list = np.empty(0, dtype=str)
        self.HASH_HEX_list = np.empty(0, dtype=str)
        self.COLLAGE_PATH_list = np.empty(0, dtype=str)
        self.BITS_IN_HASH_list = np.empty(0, dtype=str)
        for i, path in enumerate(self.PATH_list):
            logging.debug("Hashing video from {}.".format(path))
            #* Hash video
            videohash = VideoHash(path)
            videohash.similar_percentage = self.similar_percentage
            #* Save data to list
            self.VideoHash_list.append(videohash)
            self.HASH_list = np.append(self.HASH_list, videohash.hash)
            self.HASH_HEX_list = np.append(self.HASH_HEX_list, videohash.hash_hex)
            self.COLLAGE_PATH_list = np.append(self.COLLAGE_PATH_list, videohash.collage_path)
            self.BITS_IN_HASH_list = np.append(self.BITS_IN_HASH_list, videohash.bits_in_hash)
            print("Hashed {}/{} videos.".format(i+1, self.PATH_list.shape[0]), end="\r")
        if self.HASH_list.shape[0] != self.PATH_list.shape[0]:
            logging.warning("Some videos are not hashed.")
        self.video_detail_dataframe["HASH"] = self.HASH_list
        self.video_detail_dataframe["HASH_HEX"] = self.HASH_HEX_list
        self.video_detail_dataframe["COLLAGE_PATH"] = self.COLLAGE_PATH_list
        self.video_detail_dataframe["BITS_IN_HASH"] = self.BITS_IN_HASH_list
        del self.URL_list, self.HASH_list, self.HASH_HEX_list, self.COLLAGE_PATH_list, self.BITS_IN_HASH_list
        logging.debug("Hashed video list: {}".format(self.VideoHash_list))
        logging.info("Hashed {} videos.".format(len(self.VideoHash_list)))
        print("Video hashing phase complete.")
        if self.export_video_detail != False:
            export_path = os.path.join(self.export_video_detail, "video_detail.csv")
            export_path = os.path.abspath(export_path)
            self.video_detail_dataframe.to_csv(export_path, index=False)
            print("Exported video detail to {}.".format(export_path))
    
    def _compare_video(self) -> None:
        #* Compare video
        self.comparison_dataframe = pd.DataFrame(columns=["vid1_idx", "vid2_idx", "similarity"])
        self.comparison_vid1_idx_list = np.empty(0, dtype=int)
        self.comparison_vid2_idx_list = np.empty(0, dtype=int)
        self.comparison_result_list = np.empty(0, dtype=bool)
        for i, j in itertools.combinations(self.VideoHash_list, 2):
            self.comparison_vid1_idx_list = np.append(self.comparison_vid1_idx_list, self.VideoHash_list.index(i))
            self.comparison_vid2_idx_list = np.append(self.comparison_vid2_idx_list, self.VideoHash_list.index(j))
            self.comparison_result_list = np.append(self.comparison_result_list, i.is_similar(j))
        self.comparison_dataframe["vid1_idx"] = self.comparison_vid1_idx_list
        self.comparison_dataframe["vid2_idx"] = self.comparison_vid2_idx_list
        self.comparison_dataframe["similarity"] = self.comparison_result_list
        del self.comparison_vid1_idx_list, self.comparison_vid2_idx_list, self.comparison_result_list
        logging.debug("Comparison dataframe: {}".format(self.comparison_dataframe))
        logging.info("Comparison dataframe generated.")
        print("Video comparison phase complete.")
        if self.export_comparison_result != False:
            export_path = os.path.join(self.export_comparison_result, "comparison_result.csv")
            export_path = os.path.abspath(export_path)
            self.comparison_dataframe.to_csv(export_path, index=False)
            print("Exported comparison result to {}.".format(export_path))

    def _remove_cache(self) -> None:
        #* Remove cache
        for i, path in enumerate(self.PATH_list):
            logging.debug("Removing cache from {}.".format(self.VideoHash_list[i].collage_path))
            os.remove(self.VideoHash_list[i].collage_path)
            if self.remove_cache == True:
                logging.debug("Removing video file from {}.".format(path))
                os.remove(path)
        logging.info("Removed {} files.".format(len(self.PATH_list)))
        print("Cache removing phase complete.")

if __name__ == "__main__":
    filepath = "./URL_list.csv"
    cache_path = "./cache"
    tester = VideoSimilarityTester(filepath, cache_path, export_video_detail=cache_path, export_comparison_result=cache_path, similar_percentage=10)