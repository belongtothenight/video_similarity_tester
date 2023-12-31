# video_similarity_tester

This repo aims for developing a automatic batch video similarity tester.

## Requirement

**FFMPEG**

On windows, download [Chocolatey](https://chocolatey.org/install), and use it to install ffmpeg with command "choco install ffmpeg" in cmd/pwsh/pwsh7.

## Usage

[Click here to see demo video.](https://youtu.be/900zgVB_6vA)

### 1. Create CSV

Format your CSV file content to be either in **[PATH](https://github.com/belongtothenight/video_similarity_tester/blob/main/src/PATH_list.csv)** or **[YouTubeURL](https://github.com/belongtothenight/video_similarity_tester/blob/main/src/URL_list.csv)**

### 2. Execute

Python environment:
```
python main.py ./URL.csv ./cache ./cache --remove-cache --weight=0.7
```

Downloaded release: ([Download](https://github.com/belongtothenight/video_similarity_tester/releases/tag/v1.0.0))
```
vst_v1.2.0.exe ./PATH.csv ./cache ./cache --remove-cache --weight=0.7
```

Help message:
```
python main.py <input_file> <cache_path> <export_result_path> [--remove-cache] [--weight=<weight>] [-h/--help]

For URL links: ONLY ACCEPT YOUTUBE LINKS

Weight calculation: (hash_similarity * weight) + (fingerprint_similarity * (1-weight))

sys.argv[1] path of list file
sys.argv[2] path of cache folder
sys.argv[3] path of export result folder
sys.argv[?] (--remove-cache) remove cache after execution
sys.argv[?] (--weight) weight of videohash method (default: 0.7)
sys.argv[?] (-h/--help) help (show available options)
```

### 3. Check Output

The program will generate the results in your specified location, like **[VideoDetail](https://github.com/belongtothenight/video_similarity_tester/blob/main/src/cache/video_detail.csv)** and **[ComparisonResult](https://github.com/belongtothenight/video_similarity_tester/blob/main/src/cache/comparison_result.csv)**

### 4. Error

If any error occurs, please send the "./vst.log" file to me for further debugging.
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

## EXE command

```pyinstaller "./main.py" --noconfirm --onefile --console --clean --name="vst_v1.4.0"```
