import shutil

import numpy as np
from detector import Detector
from attacks import attack
from utils2 import load_json_file, get_results, load_caption_file, load_standard_json
import os
from tqdm import tqdm
import time

from captum.attr import IntegratedGradients
from captum.attr import visualization
import torch
'''
The dataset originally given into this model is 100% synthetic, generated by GPT-2. we are trying to see if they can be fooled for human
There are different types of attacks/experiments organized by keyword in the attacks.py file

EXPERIMENT_NAME is the name of the folder to hold the data files
ADVERSARIAL_TYPE is the type of changes we make to each text.
IMAGES_TO_RUN is the number of image captions to make adversarial.

Adversarial Types:
-'do-nothing': Nothing is done
-'replace-char': Replace homoglyphs below
-'random-order-replace-char': Same as replace char except the input text lines are shuffled
-'misspelling': Replaces certain words with misspellings from misspellings.json.
'''
HUMAN_MUTATION, REAL, SYNTHETIC, SYNTHETIC_MUTATION = 0, 1, 2, 3

EXPERIMENT_NAME = "CheckHumanMutations"
DATASET_TYPE = HUMAN_MUTATION
CHECK_BY_IMAGE = True
ADVERSARIAL_TYPE = "do-nothing"
# DATA_FILE = './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullSet.json'
# DATA_FILE = './data/synthetic_mutation/Test_WikiSyntheticMutationFullSet.json'
# DATA_FILE = './data/human_mutation/Test_WikiHumanMutationFullSet.json'
# DATA_FILE = './data/Test_WikiHumanFullSet.json'
# DATA_FILE = './data/Test_WikiHumanQuarterSet.json'
# DATA_FILE = './data/Test_WikiMutationFullReplaceAntonyms.json'
# DATA_FILE = './data/Test_WikiMutationFullReplaceRandomWords.json'
# DATA_FILE = './data/Test_WikiMutationFullReplaceSynonyms.json'
# DATA_FILE = './data/Test_WikiMutationFullSet.json'
# DATA_FILE = './data/Test_WikiMutationFullSetDeleteArticles.json'
# DATA_FILE = './data/Test_WikiMutationFullSetMisspellings.json'
# DATA_FILE = './data/Test_WikiMutationFullSetReplaceAE.json'
# DATA_FILE = './data/Test_WikiMutationQuarterSet.json'
# DATA_FILE = './data/Test_WikiChatGPTSyntheticFullSet.json'
# DATA_FILE = './data/Test_WikiSyntheticFullSet.json'
# DATA_FILE = './data/Test_WikiSyntheticQuarterSet.json'
DETECTOR_FILE = "./4GPT3Model.pt.pt"
HOMOGLYPH_REPLACEMENT = [[' a ', ' α ']]
TEXTS_TO_RUN = 200

TEXTS_TO_RUN *= (1 if CHECK_BY_IMAGE else 5) # run 5 captions individually when not by image
adv_textList = []
results = []
num_ch = []
def run_experiment(
	file,
	homoglyphs,
	attack_type, 
	detector,
	experiment_name,
	percent_change = None,
	misspelling_dict = None,
	throwout=False):
	global adv_textList, results, num_ch
	start_time = time.time()

	print('Running Experiment: {} ...'.format(experiment_name))

	text_list = []
	if 'xl-1542M-k40' in file:
		text_list = load_json_file(file)
	if 'xl-1542M-k40' not in file:
		if ".json" in file:
			text_list = load_standard_json(file, CHECK_BY_IMAGE)
		else:
			text_list = load_caption_file(file, CHECK_BY_IMAGE)

	_range = tqdm(range(TEXTS_TO_RUN))#len(text_list)))
	i = 0


	for _ in _range:
		text_to_use = detector.tokenizer.decode(
			detector.tokenizer.encode(text_list[i], max_length=detector.tokenizer.max_len))[3:-4]


		adv_text, num_changes = attack(
			text_to_use, homoglyphs, attack_type, percent_change, misspelling_dict, throwout)
		if throwout and (adv_text==text_to_use):
			pass

		else:

			adv_textList.append(adv_text)
			probs = detector.predict(adv_text)
			pred = probs.tolist().index(max(probs))

			_range.set_description('{} | {}'.format(i, pred))

			results.append(str(pred))
			num_ch.append(str(num_changes))

		i+=1
	end_time = time.time()

	print('Time to complete experiment (minutes):', (end_time-start_time)/60.)


import wget
if __name__ == '__main__':
	detector = Detector(DETECTOR_FILE)

	# file2 = [DATA_FILE]

	files = ['./data/human_mutation/Test_WikiHumanMutationFullReplaceAntonyms.json', './data/human_mutation/Test_WikiHumanMutationFullReplaceRandomWords.json',
	 './data/human_mutation/Test_WikiHumanMutationFullReplaceSynonyms.json', './data/human_mutation/Test_WikiHumanMutationFullSetDeleteArticles.json',
	 './data/human_mutation/Test_WikiHumanMutationFullSetMisspellings.json', './data/human_mutation/Test_WikiHumanMutationFullSetReplaceAE.json']

	# files = ['./data/synthetic_mutation/Test_WikiSyntheticMutationFullReplaceAntonyms.json', './data/synthetic_mutation/Test_WikiSyntheticMutationFullReplaceRandomWords.json',
	# 	 './data/synthetic_mutation/Test_WikiSyntheticMutationFullReplaceSynonyms.json', './data/synthetic_mutation/Test_WikiSyntheticMutationFullSetDeleteArticles.json',
	# 	 './data/synthetic_mutation/Test_WikiSyntheticMutationFullSetMisspellings.json', './data/synthetic_mutation/Test_WikiSyntheticMutationFullSetReplaceAE.json']

	# files = ['./data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullReplaceAntonyms.json', './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullReplaceRandomWords.json',
	# 	 './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullReplaceSynonyms.json', './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullSetDeleteArticles.json',
	# 	 './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullSetMisspellings.json', './data/synthetic_mutation/Test_WikiChatGPTSyntheticMutationFullSetReplaceAE.json']


	for file in files:
		EXPERIMENT_NAME = file
		adv_textList = []
		results = []
		num_ch = []
		run_experiment(
			file,#DATA_FILE
			HOMOGLYPH_REPLACEMENT,
			ADVERSARIAL_TYPE,
			detector,
			EXPERIMENT_NAME,
			None,
			None,
			None)

		get_results(EXPERIMENT_NAME, DATASET_TYPE, adv_textList, results, num_ch)


