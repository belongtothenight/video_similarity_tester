from videohash import VideoHash
from pytube import YouTube
import videofingerprint as vfp
import pandas as pd
import numpy as np
import csv
import logging
import os
import itertools
import sys
import getopt
import subprocess

def config_logging() -> None:
    logger_file_path = "./vst.log"
    # level = logging.DEBUG
    level = logging.INFO
    # level = logging.WARNING
    # level = logging.ERROR
    # level = logging.CRITICAL
    if os.path.exists(logger_file_path):
        os.remove(logger_file_path)
    logging.basicConfig(filename=logger_file_path, level=level, format='%(asctime)s - %(levelname)s %(name)s - %(message)s')
    logger = logging.getLogger(__name__)
    return logger

class VST_Error:
    def __init__(self, logger) -> None:
        # self.error_str = "\033[91m"
        # self.end_str = "\033[0m"
        self.error_str = "ERROR: "
        self.end_str = " ERROR"
        self.logger = logger
        
    def argument_not_enough(self) -> None:
        print("{}Argument is not enough.{}".format(self.error_str, self.end_str))
        sys.exit()

    def invalid_argument(self, argument:str) -> None:
        print("{}Invalid argument contained in {}.{}".format(self.error_str, argument, self.end_str))
        sys.exit()

    def path_not_exist(self, path: str) -> None:
        print("{}Path {} does not exist.{}".format(self.error_str, path, self.end_str))
        sys.exit()

    def file_not_exist(self, file: str) -> None:
        print("{}File {} does not exist.{}".format(self.error_str, file, self.end_str))
        sys.exit()

    def dependency_not_found(self, dependency: str) -> None:
        print("{}Dependency {} not found.{}".format(self.error_str, dependency, self.end_str))
        self.logger.exception("Dependency {} not found.".format(dependency))
        sys.exit()

    def general_error(self, error: str) -> None:
        print("{}General error: {}.{}".format(self.error_str, error, self.end_str))
        self.logger.exception(error)
        sys.exit()

class VST_Warning:
    def __init__(self, logger) -> None:
        # self.warning_str = "\033[93m"
        # self.end_str = "\033[0m"
        self.warning_str = "WARNING: "
        self.end_str = "WARNING"
        self.logger = logger

    def action_failed(self, action: str) -> None:
        print("{}Action {} failed.{}".format(self.warning_str, action, self.end_str))

    def general_warning(self, warning: str) -> None:
        print("{}General warning: {}.{}".format(self.warning_str, warning, self.end_str))
        self.logger.warning(warning)

class VideoSimilarityTester:
    #* Class to test similarity between videos
    def __init__(self, cache_path:str, URL_list_filepath=None, PATH_list_filepath=None, download_resolution=0, export_video_detail=False, export_comparison_result=False, remove_cache=True, method_weight=[0.7, 0.3]) -> None:
        #* Check input method (URL list or PATH list)
        if URL_list_filepath == None and PATH_list_filepath == None:
            logging.critical("URL list or PATH list must be provided.")
            vst_error.argument_not_enough()
        self.input_method = "URL_list" if URL_list_filepath != None else "PATH_list"
        #* Initialize class
        self.URL_list_filepath = URL_list_filepath
        self.PATH_list_filepath = PATH_list_filepath
        self.cache_path = cache_path
        self.download_resolution = download_resolution
        self.export_video_detail = export_video_detail
        self.export_comparison_result = export_comparison_result
        self.remove_cache = remove_cache
        self.method_weight = method_weight
        #* Check if path is valid
        if self.input_method == "URL_list":
            if not os.path.exists(self.URL_list_filepath):
                logging.critical("URL list file does not exist.")
                vst_error.path_not_exist(self.URL_list_filepath)
        elif self.input_method == "PATH_list":
            if not os.path.exists(self.PATH_list_filepath):
                logging.critical("PATH list file does not exist.")
                vst_error.path_not_exist(self.PATH_list_filepath)
        if not os.path.exists(self.cache_path):
            logging.critical("Cache path does not exist.")
            vst_error.path_not_exist(self.cache_path)
        if self.export_video_detail != False:
            if not os.path.exists(self.export_video_detail):
                logging.critical("Export video detail path does not exist.")
                vst_error.path_not_exist(self.export_video_detail)
        if self.export_comparison_result != False:
            if not os.path.exists(self.export_comparison_result):
                logging.critical("Export comparison result path does not exist.")
                vst_error.path_not_exist(self.export_comparison_result)
        #* Create variable
        self.download_retry = 5
        self.videohash_retry = 3
        self.fingerprint_retry = 3
        self.URL_list = np.empty(0, dtype=str)
        self.video_detail_dataframe = pd.DataFrame(columns=["URL", "TITLE", "PATH", "HASH", "HASH_HEX", "COLLAGE_PATH", "BITS_IN_HASH", "FINGER_PRINT"])
        self.PATH_list = np.empty(0, dtype=str)
        self.TITLE_list = np.empty(0, dtype=str)
        self.VideoHash_list = []
        self.HASH_list = np.empty(0, dtype=str)
        self.HASH_HEX_list = np.empty(0, dtype=str)
        self.COLLAGE_PATH_list = np.empty(0, dtype=str)
        self.BITS_IN_HASH_list = np.empty(0, dtype=str)
        self.FINGER_PRINT_list = np.empty(0, dtype=str)
        self.comparison_dataframe = pd.DataFrame(columns=["vid1_idx", "vid2_idx", "mix_idx", "hash_similarity", "fingerprint_similarity", "avg_similarity"])
        self.comparison_vid1_idx_list = np.empty(0, dtype=int)
        self.comparison_vid2_idx_list = np.empty(0, dtype=int)
        self.comparison_mix_idx_list = np.empty(0, dtype=str)
        self.comparison_result_list1 = np.empty(0, dtype=float)
        self.comparison_result_list2 = np.empty(0, dtype=float)
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
        if self.export_video_detail != False:
            self._write_video_detail()
        self._generate_result()
        self._remove_cache()

    def _load_URL_list(self) -> None:
        with open(self.input_filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                self.URL_list = np.append(self.URL_list, row[0])
        self.video_detail_dataframe["URL"] = self.URL_list
        logging.debug("Loaded URL list: {}".format(self.URL_list))
        logging.info("Loaded URL list from {} with {} {} files.".format(self.URL_list_filepath, self.URL_list.shape[0], self.URL_list.shape))
        print("URL list loading phase complete, loaded {} URLs.".format(self.URL_list.shape[0]))

    def _load_PATH_list(self) -> None:
        self.PATH_list = np.empty(0, dtype=str)
        with open(self.input_filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                self.PATH_list = np.append(self.PATH_list, row[0])
        self.video_detail_dataframe["PATH"] = self.PATH_list
        logging.debug("Loaded PATH list: {}".format(self.PATH_list))
        logging.info("Loaded PATH list from {} with {} {} files.".format(self.PATH_list_filepath, self.PATH_list.shape[0], self.PATH_list.shape))
        print("PATH list loading phase complete, loaded {} PATHs.".format(self.PATH_list.shape[0]))

    def _download_video(self) -> None:
        #* Download video from URL
        for i, url in enumerate(self.URL_list):
            logging.debug("Downloading video from {}.".format(url))
            path = os.path.join(self.cache_path, str(i)+".mp4")
            path = os.path.abspath(path)
            logging.debug("Saving file is: ".format(path))
            tmp_download_retry = self.download_retry
            while (tmp_download_retry > 0):
                try:
                    #* Download video from URL & Save video to file
                    yt = YouTube(url)
                    yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first().download(filename=path)
                    #* Save data to list
                    self.PATH_list = np.append(self.PATH_list, path)
                    self.TITLE_list = np.append(self.TITLE_list, yt.title)
                    break
                except Exception as e:
                    vst_warning.general_warning(e)
                    logging.warning("Failed to download {}th video from {}. Try count: {}".format(i+1, url, self.download_retry-tmp_download_retry+1))
                    print("Failed to download {}th video from {}. Try count: {}".format(i+1, url, self.download_retry-tmp_download_retry+1))
                    tmp_download_retry -= 1
                    if tmp_download_retry == 0:
                        logging.warning("Failed to download {}th video from {} after {} retries.".format(i+1, url, self.download_retry))
                        vst_warning.action_failed("download video")
                        self.PATH_list = np.append(self.PATH_list, "")
                        self.TITLE_list = np.append(self.TITLE_list, "")
            print("Downloading {}/{} videos...".format(i+1, self.URL_list.shape[0]), end="\r")
        print("Downloading {}/{} videos... OK".format(i+1, self.URL_list.shape[0]))
        if self.PATH_list.shape[0] != self.URL_list.shape[0]:
            logging.warning("Some videos are not downloaded.")
            vst_warning.action_failed("download video")
        self.video_detail_dataframe["PATH"] = self.PATH_list
        self.video_detail_dataframe["TITLE"] = self.TITLE_list
        logging.debug("Downloaded video list: {}".format(self.PATH_list))
        logging.info("Downloaded {} videos.".format(self.PATH_list.shape[0]))
        print("Video downloading phase complete.")

    def _hash_video(self) -> None:
        #* Hash video
        for i, path in enumerate(self.PATH_list):
            logging.debug("Hashing video from {}.".format(path))
            tmp_videohash_retry = self.videohash_retry
            while (tmp_videohash_retry > 0):
                try:
                    #* Hash video
                    videohash = VideoHash(path)
                    #* Save data to list
                    self.VideoHash_list.append(videohash)
                    self.HASH_list = np.append(self.HASH_list, videohash.hash)
                    self.HASH_HEX_list = np.append(self.HASH_HEX_list, videohash.hash_hex)
                    self.COLLAGE_PATH_list = np.append(self.COLLAGE_PATH_list, videohash.collage_path)
                    self.BITS_IN_HASH_list = np.append(self.BITS_IN_HASH_list, videohash.bits_in_hash)
                    break
                except videohash.exceptions.FFmpegNotFound:
                    vst_error.dependency_not_found("FFmpeg")
                except Exception as e:
                    vst_warning.general_warning(e)
                    logging.warning("Failed to hash {}th video from {}. Try count: {}".format(i+1, path, self.videohash_retry-tmp_videohash_retry+1))
                    print("Failed to hash {}th video from {}. Try count: {}".format(i+1, path, self.videohash_retry-tmp_videohash_retry+1))
                    temp_videohash_retry -= 1
                    if tmp_videohash_retry == 0:
                        logging.warning("Failed to hash {}th video from {} after {} retries".format(i+1, path, self.videohash_retry))
                        vst_warning.action_failed("hash video")
                        self.VideoHash_list.append(None)
                        self.HASH_list = np.append(self.HASH_list, "")
                        self.HASH_HEX_list = np.append(self.HASH_HEX_list, "")
                        self.COLLAGE_PATH_list = np.append(self.COLLAGE_PATH_list, "")
                        self.BITS_IN_HASH_list = np.append(self.BITS_IN_HASH_list, "")
            print("Hashing {}/{} videos...".format(i+1, self.PATH_list.shape[0]), end="\r")
        print("Hashing {}/{} videos... OK".format(i+1, self.PATH_list.shape[0]))
        if self.HASH_list.shape[0] != self.PATH_list.shape[0]:
            logging.warning("Some videos are not hashed.")
            vst_warning.action_failed("hash video")
        self.video_detail_dataframe["HASH"] = self.HASH_list
        self.video_detail_dataframe["HASH_HEX"] = self.HASH_HEX_list
        self.video_detail_dataframe["COLLAGE_PATH"] = self.COLLAGE_PATH_list
        self.video_detail_dataframe["BITS_IN_HASH"] = self.BITS_IN_HASH_list
        logging.debug("Hashed video list: {}".format(self.HASH_list))
        logging.info("Hashed {} videos.".format(self.HASH_list.shape[0]))
        print("Video hashing phase complete.")
    
    def _finger_print_video(self) -> None:
        #* Fingerprint video
        for i, path in enumerate(self.PATH_list):
            logging.debug("Fingerprinting video from {}.".format(path))
            tmp_fingerprint_retry = self.fingerprint_retry
            while (tmp_fingerprint_retry > 0):
                try:
                    #* Fingerprint video
                    vp = vfp.VideoFingerprint(path)
                    #* Save data to list
                    self.FINGER_PRINT_list = np.append(self.FINGER_PRINT_list, vp.fingerprint)
                    break
                except Exception as e:
                    vst_warning.general_warning(e)
                    logging.warning("Failed to fingerprint {}th video from {}. Try count: {}".format(i+1, path, self.fingerprint_retry-tmp_fingerprint_retry+1))
                    print("Failed to fingerprint {}th video from {}. Try count: {}".format(i+1, path, self.fingerprint_retry-tmp_fingerprint_retry+1))
                    tmp_fingerprint_retry -= 1
                    if tmp_fingerprint_retry == 0:
                        logging.warning("Failed to fingerprint {}th video from {} after {} retries".format(i+1, path, self.fingerprint_retry))
                        vst_warning.action_failed("fingerprint video")
                        self.FINGER_PRINT_list = np.append(self.FINGER_PRINT_list, "")
            print("Fingerprinting {}/{} videos...".format(i+1, self.PATH_list.shape[0]), end="\r")
        print("Fingerprinting {}/{} videos... OK".format(i+1, self.PATH_list.shape[0]))
        if self.FINGER_PRINT_list.shape[0] != self.PATH_list.shape[0]:
            logging.warning("Some videos are not fingerprinted.")
            vst_warning.action_failed("fingerprint video")
        self.video_detail_dataframe["FINGER_PRINT"] = self.FINGER_PRINT_list
        logging.debug("Fingerprinted video list: {}".format(self.FINGER_PRINT_list))
        logging.info("Fingerprinted {} videos.".format(self.FINGER_PRINT_list.shape[0]))
        print("Video fingerprinting phase complete.")

    def _write_video_detail(self) -> None:
        export_path = os.path.join(self.export_video_detail, "video_detail.csv")
        export_path = os.path.abspath(export_path)
        self.video_detail_dataframe.to_csv(export_path, index=False)
        logging.info("Exported video detail to {}.".format(export_path))
        print("Exported video detail to {}.".format(export_path))

    def _generate_result(self) -> None:
        #* Compare video
        index_list = np.arange(len(self.PATH_list))
        for cmp_obj_1, cmp_obj_2 in itertools.combinations(index_list, 2):
            self.comparison_vid1_idx_list = np.append(self.comparison_vid1_idx_list, cmp_obj_1)
            self.comparison_vid2_idx_list = np.append(self.comparison_vid2_idx_list, cmp_obj_2)
            self.comparison_mix_idx_list = np.append(self.comparison_mix_idx_list, str(cmp_obj_1)+"-"+str(cmp_obj_2))
            #! Abandoned using VideoHash.is_similar() because it shows too little information
            # self.comparison_result_list1 = np.append(self.comparison_result_list1, i.is_similar(j))
            try:
                self.comparison_result_list1 = np.append(self.comparison_result_list1, self.__compare_code(self.VideoHash_list[cmp_obj_1].hash, self.VideoHash_list[cmp_obj_2].hash))
            except Exception as e:
                logging.warning("Failed to compare hash data from VideoHash_list of {}th video with {}th video.".format(cmp_obj_1+1, cmp_obj_2+1))
                vst_warning.general_warning(e)
                self.comparison_result_list1 = np.append(self.comparison_result_list1, 0)
            try:
                self.comparison_result_list2 = np.append(self.comparison_result_list2, self.__compare_code(self.FINGER_PRINT_list[cmp_obj_1], self.FINGER_PRINT_list[cmp_obj_2]))
            except Exception as e:
                logging.warning("Failed to compare fingerprint data from FINGER_PRINT_list of {}th video with {}th video.".format(cmp_obj_1+1, cmp_obj_2+1))
                vst_warning.general_warning(e)
                self.comparison_result_list2 = np.append(self.comparison_result_list2, 0)
        self.comparison_dataframe["vid1_idx"] = self.comparison_vid1_idx_list
        self.comparison_dataframe["vid2_idx"] = self.comparison_vid2_idx_list
        self.comparison_dataframe["mix_idx"] = self.comparison_mix_idx_list
        #* Individual similarity boost
        self.comparison_dataframe["hash_similarity"] = self.comparison_result_list1
        self.comparison_dataframe["fingerprint_similarity"] = (self.comparison_result_list2 - self.comparison_result_list2.min()) / (self.comparison_result_list2.max() - self.comparison_result_list2.min()) #* Normalize fingerprint similarity
        self.comparison_dataframe["avg_similarity"] = (self.comparison_dataframe["hash_similarity"] * self.method_weight[0]) + (self.comparison_dataframe["fingerprint_similarity"] * self.method_weight[1])
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
            try:
                os.remove(self.VideoHash_list[i].collage_path)
            except Exception as e:
                logging.warning("Failed to remove cache from {}.".format(self.VideoHash_list[i].collage_path))
                vst_warning.general_warning(e)
            if self.remove_cache == True:
                logging.debug("Removing video file from {}.".format(path))
                try:
                    os.remove(path)
                except Exception as e:
                    logging.warning("Failed to remove video file from {}.".format(path))
                    vst_warning.general_warning(e)
        logging.info("Removed {} files.".format(len(self.PATH_list)))
        print("Cache removing phase complete.")

    def __compare_code(self, vid1_code: str, vid2_code: str) -> None:
        #* Check two code should be same length
        if len(vid1_code) != len(vid2_code):
            """
            Perform bigram comparison between two strings
            and return a percentage match in decimal form.
            """
            pairs1 = self.___get_bigrams(vid1_code)
            pairs2 = self.___get_bigrams(vid2_code)
            union  = len(pairs1) + len(pairs2)
            hit_count = 0
            for x in pairs1:
                for y in pairs2:
                    if x == y:
                        hit_count += 1
                        break
            return (2.0 * hit_count) / union
        else:
            #* Compare two code
            diffcnt = 0
            for i in range(len(vid1_code)):
                if vid1_code[i] != vid2_code[i]:
                    diffcnt += 1
            return (len(vid1_code) - diffcnt) / len(vid1_code)
    
    def ___get_bigrams(self, string):
        """
        Take a string and return a list of bigrams.
        """
        s = string.lower()
        return [s[i:i+2] for i in list(range(len(s) - 1))]

def input_file_check(input_filepath: str) -> None:
    #* Check if path is valid
    if not os.path.exists(input_filepath):
        logging.critical("Input file does not exist.")
        vst_error.path_not_exist(input_filepath)
    #* Read first line
    with open(input_filepath, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            first_line = row
            break
    #* Check if first line is URL or PATH
    if first_line[0].startswith("http"):
        input_method = "URL_list"
    else:
        input_method = "PATH_list"
    return input_method

def ffmpeg_check() -> None:
    #* Check if FFmpeg is installed
    print("Checking FFmpeg...", end="\r")
    try:
        subprocess.check_output(["ffmpeg", "-version"])
        installed = True
    except FileNotFoundError:
        vst_error.dependency_not_found("FFmpeg")
    print("Checking FFmpeg...OK")

def execute():
    """
    Video Similarity Tester
    Usage: python main.py <input_file> <cache_path> <export_result_path> [--remove-cache] [--weight=<weight>] [-h/--help]
    !!!For URL links: ONLY ACCEPT YOUTUBE LINKS!!!
    Weight calculation: (hash_similarity * weight) + (fingerprint_similarity * (1-weight))
    sys.argv[1] path of list file
    sys.argv[2] path of cache folder
    sys.argv[3] path of export result folder
    sys.argv[?] (--remove-cache) remove cache after execution
    sys.argv[?] (--weight) weight of videohash method (default: 0.7)
    sys.argv[?] (-h/--help) help (show available options)
    """
    #* Check arguments
    available_short_options = "h:"
    available_long_options = ["remove-cache", "weight=", "help"]
    try:
        opts, args = getopt.getopt(sys.argv[4:], available_short_options, available_long_options)
    except getopt.GetoptError:
        logging.critical("Invalid arguments.")
        vst_error.invalid_argument(sys.argv[4:])
    logging.info("Arguments checked.")
    #* Check for help
    if len(sys.argv) < 4:
        if '-h' in sys.argv or '--help' in sys.argv:
            print(execute.__doc__)
            sys.exit()
        else:
            logging.critical("Not enough arguments.")
            vst_error.argument_not_enough()
    logging.info("Help checked.")
    #* Initialize variable
    remove_cache = False
    method_weight = 0.7
    list_filepath = sys.argv[1]
    cache_path = sys.argv[2]
    export_result_path = sys.argv[3]
    logging.info("Initialized variable.")
    #* Parse arguments
    for opt, arg in opts:
        if opt in ("--remove-cache"):
            remove_cache = True
        elif opt in ("--weight"):
            method_weight = float(arg)
    logging.info("Parsed arguments.")
    #* Check input method (URL list or PATH list)
    input_method = input_file_check(list_filepath)
    logging.info("Input method checked.")
    #* Check if FFmpeg is installed
    ffmpeg_check()
    logging.info("FFmpeg checked.")
    #* Call class
    if input_method == "URL_list":
        VideoSimilarityTester(cache_path=cache_path, URL_list_filepath=list_filepath, export_video_detail=export_result_path, export_comparison_result=export_result_path, remove_cache=remove_cache, method_weight=[method_weight, 1-method_weight])
    elif input_method == "PATH_list":
        VideoSimilarityTester(cache_path=cache_path, PATH_list_filepath=list_filepath, export_video_detail=export_result_path, export_comparison_result=export_result_path, remove_cache=remove_cache, method_weight=[method_weight, 1-method_weight])

if __name__ == "__main__":
    # URL_filepath = "./URL_list.csv"
    # PATH_filepath = "./PATH_list.csv"
    # cache_path = "./cache"
    # # VideoSimilarityTester(cache_path=cache_path, URL_list_filepath=URL_filepath, export_video_detail=cache_path, export_comparison_result=cache_path, remove_cache=False)
    # VideoSimilarityTester(cache_path=cache_path, PATH_list_filepath=PATH_filepath, export_video_detail=cache_path, export_comparison_result=cache_path, remove_cache=False)
    #* Initialize logger
    logger = config_logging()
    logging.info("Initialized logger.")
    #* Initialize VST classes
    vst_error = VST_Error(logger=logger)
    vst_warning = VST_Warning(logger=logger)
    logging.info("Initialized VST classes.")
    #* Execute program
    try:
        execute()
    except Exception as e:
        vst_error.general_error(e)