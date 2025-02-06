# CliniDigest PubMed

3-stage pipeline for extracting PubMed clinical trials, and automatically summarizing them.

First, install the Python dependencies using `pip install -r requirements.txt`. After adding a DeepSeek API key to `API_KEY_PATH` in `run.sh`, just run `./run.sh`.

To run each stage individually for debugging or testing, each part takes command line arguments, run `python3 [filename].py` to display the arguments.
