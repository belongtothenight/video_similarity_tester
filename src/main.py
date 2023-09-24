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
    def __init__(self, cache_path:str, URL_list_filepath=None, PATH_list_filepath=None, download_resolution=0, export_video_detail=False, export_comparison_result=False, remove_cache=True, similar_percentage=15) -> None:
        #* Check input method (URL list or PATH list)
        if URL_list_filepath == None and PATH_list_filepath == None:
            logging.critical("URL list or PATH list must be provided.")
            raise Exception("URL list or PATH list must be provided.")
        self.input_method = "URL_list" if URL_list_filepath != None else "PATH_list"
        #* Initialize class
        self.URL_list_filepath = URL_list_filepath
        self.PATH_list_filepath = PATH_list_filepath
        self.cache_path = cache_path
        self.download_resolution = download_resolution
        self.export_video_detail = export_video_detail
        self.export_comparison_result = export_comparison_result
        self.remove_cache = remove_cache
        self.similar_percentage = similar_percentage
        #* Check if path is valid
        if self.input_method == "URL_list":
            if not os.path.exists(self.URL_list_filepath):
                logging.critical("URL list file does not exist.")
                raise Exception("URL list file does not exist.")
        elif self.input_method == "PATH_list":
            if not os.path.exists(self.PATH_list_filepath):
                logging.critical("PATH list file does not exist.")
                raise Exception("PATH list file does not exist.")
        if not os.path.exists(self.cache_path):
            logging.critical("Cache path does not exist.")
            raise Exception("Cache path does not exist.")
        if self.export_video_detail != False:
            if not os.path.exists(self.export_video_detail):
                logging.critical("Export video detail path does not exist.")
                raise Exception("Export video detail path does not exist.")
        if self.export_comparison_result != False:
            if not os.path.exists(self.export_comparison_result):
                logging.critical("Export comparison result path does not exist.")
                raise Exception("Export comparison result path does not exist.")
        #* Create variable
        self.URL_list = np.empty(0, dtype=str)
        self.video_detail_dataframe = pd.DataFrame(columns=["URL", "PATH", "HASH", "HASH_HEX", "COLLAGE_PATH", "BITS_IN_HASH"])
        #* Call next function on the line
        if self.input_method == "URL_list":
            self.input_filepath = self.URL_list_filepath
            self._load_URL_list()
            self._download_video()
        elif self.input_method == "PATH_list":
            self.input_filepath = self.PATH_list_filepath
            self._load_PATH_list()
        self._hash_video()
        self._finger_print_video()
        self._compare_video()
        self._remove_cache()

    def _load_URL_list(self) -> None:
        with open(self.input_filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                self.URL_list = np.append(self.URL_list, row[0])
        self.video_detail_dataframe["URL"] = self.URL_list
        logging.debug("Loaded URL list: {}".format(self.URL_list))
        logging.info("Loaded URL list from {} with {} {} files.".format(self.URL_list_filepath, self.URL_list.shape[0], self.URL_list.shape))
        print("URL list loading phase complete.")

    def _load_PATH_list(self) -> None:
        self.PATH_list = np.empty(0, dtype=str)
        with open(self.input_filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                self.PATH_list = np.append(self.PATH_list, row[0])
        self.video_detail_dataframe["PATH"] = self.PATH_list
        logging.debug("Loaded PATH list: {}".format(self.PATH_list))
        logging.info("Loaded PATH list from {} with {} {} files.".format(self.PATH_list_filepath, self.PATH_list.shape[0], self.PATH_list.shape))
        print("PATH list loading phase complete.")

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
    
    def _finger_print_video(self) -> None:
        pass

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

    def __compare_result(self, vid1_code, vid2_code) -> None:
        pass


if __name__ == "__main__":
    URL_filepath = "./URL_list.csv"
    PATH_filepath = "./PATH_list.csv"
    cache_path = "./cache"
    # VideoSimilarityTester(cache_path=cache_path, URL_list_filepath=URL_filepath, export_video_detail=cache_path, export_comparison_result=cache_path, similar_percentage=10, remove_cache=False)
    VideoSimilarityTester(cache_path=cache_path, PATH_list_filepath=PATH_filepath, export_video_detail=cache_path, export_comparison_result=cache_path, similar_percentage=10, remove_cache=False)