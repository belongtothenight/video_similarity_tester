# video_similarity_tester

This repo aims for developing a automatic batch video similarity tester.

## Usage

1. Create a list of YouTube links of videos like "./src/URL_list.csv" or a list of vidoe path like "./src/PATH_list.csv".
2. Specify parameters and execute "./src/main.c".
3. The program will generate result files like "./src/cache/comparison_result.csv", and "./src/cache/video_detail.csv".

## Process Flow

1. Generate video hash.
2. Generate video fingerprint.
3. Compare all video combinations possible and generate corresponding similarity data.
4. Normalize fingerprint similarity data to limite data range.
5. Calculate mix similarity data with user given weight to both hash and fingerprint data.

## Reference

1. [VideoHash](https://github.com/akamhy/videohash)
2. [PyTube](https://www.the-analytics.club/download-youtube-videos-in-python/)
3. [Python - difference between two strings](https://stackoverflow.com/questions/17904097/python-difference-between-two-strings)
4. [A better similarity ranking algorithm for variable length strings](https://stackoverflow.com/questions/653157/a-better-similarity-ranking-algorithm-for-variable-length-strings)
5. [VideoFingerPrint](https://pypi.org/project/videofingerprint/)
