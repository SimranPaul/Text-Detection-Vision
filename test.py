import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('file')
args = parser.parse_args()
with open(args.file) as file:
        datastore = json.load(file)
print (datastore["office"]["parking"]["style"])
