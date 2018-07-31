# Receipt Recognizer Documentation
## Introduction
This Project was developed by Matthias Leopold for the [RFND AG](http://rfnd.com/).
The goal is to design a machine learning model, that can recognize any given receipt (to some extend). Therefore, it needs to recognize every article with its respective price, description, amount and vat class, as well as total price and vat sums.

Current status: Working on Edeka + Müller datasets. Given the Google Vision OCR-Results (further processed by Matthias), we are able to classify >99,8% of the rows correctly and extract the structured data from the rows procedural (which works decently good).

## Project structure
In the following i will describe the content of each directory
### assets
This folder is not included in git and holds the data (for each receipt), which includes the images, Matthias' OCR-results, the labels for each row (created with the labeling tool) and the preprocessed dataframes (containing the features).
### research
This folder contains experimental work and some statistics. Most interesting might be the file *vatClass_confusion_stats.xslx*, in which i have documented with which character the Google Vision-OCR confuses the actual vat classes (last char in an article row). On the basis of these statistics, we can easily handle most of the OCR miss-recognitions of the vat class.
### src
This is the source folder and contains the actual python source code. Following, i will shortly descripe its content:
* **labeler.py:** Tool to label the rows for a given receipt (img + OCR-Result)
* **preprocessing.py:** Script, that calculates the features for each row, given the OCR-Result. I append the labels for the rows here as well.
* **service.py:** The callable service, that takes the trained model/classifier and an OCR-Result of an image and returns structured data for the given receipt. The structured data consists of articles (description, price, vat-Class), totalSum, vatSums(netto, brutto, vat-Class, tax-rate), totalVatSum(netto,brutto).
* **training.py:** The script that takes a given set of preprocessed dataframes (containing the features) and trains the machine learning model/classifier. For now a Random Forest is trained.
* **utility.py:** Utility functions, used for experiments and in *training.py*
### classifier.pkl
This file in the root directory is the serialized Random Forest that was trained on the full edeka/müller data set. It is used in the *service.py*.

## Get started using the service
### Installing dependencies with pip
The *service.py* uses three external libraries: **pandas**,**sklearn**, **scipy**. Those three can be installed (optionally into a virtualenv) with pip:
```
pip install pandas sklearn scipy
```
or
```
python -m pip install pandas sklearn scipy
```

### Running the service
Afterwards, you can call the service by passing the path of the JSON file (Matthias' OCR-Result), that you want to be analysed, as command line argument. For example:
```
python service.py C:/Users/matthias/ReceiptRecognozer/assets/müllerData/tx_17_2-40.webp.json
```
The result should look something like:
```
articles:
[{'description': '1 LOREAL MEN EXPERT H  ', 'price': 5.85, 'vat': 'A'},
 {'description': '1 CLEAN PAC KAFFEE - FI  ', 'price': 0.55, 'vat': 'A'},
 {'description': '1 CILLIT BANG AKTIV  ', 'price': 2.75, 'vat': 'A'},
 {'description': '1 CILLIT BANG AKTIV  ', 'price': 2.75, 'vat': 'A'},
 {'description': '1 MERIDOL ZAHNBUERSTE  ', 'price': 2.85, 'vat': 'A'},
 {'description': '1 MONSTER ABSOLUTELY  ', 'price': 1.59, 'vat': 'A'},
 {'description': 'PFAND - EINWEG RUECKN  ', 'price': 0.25, 'vat': 'A'},
 {'description': '1 FA DEOSPRAY MEN XTR  ', 'price': 1.25, 'vat': 'A'},
 {'description': '1 GUM EXPANDING FLOSS  ', 'price': 2.25, 'vat': 'A'},
 {'description': '1 GUM EXPANDING FLOSS  ', 'price': 2.25, 'vat': 'A'},
 {'description': '1 FA DEOSPRAY MEN XTR  ', 'price': 1.25, 'vat': 'A'},
 {'description': '1 FA DUSCHE MEN SPORT  ', 'price': 1.25, 'vat': 'A'},
 {'description': 'I MERIDOL ZUNGENREINI  ', 'price': 3.45, 'vat': 'A'},
 {'description': '1 ALNATURA RAEUCHER T  ', 'price': 1.55, 'vat': 'B'},
 {'description': '1 ALNATURA TOFU NATUR  ', 'price': 1.45, 'vat': 'B'},
 {'description': '1 FA DEOSPRAY MEN KIC  ', 'price': 1.25, 'vat': 'A'},
 {'description': '1 ELMEX ZAHNSPUELUNG  ', 'price': 4.55, 'vat': 'A'},
 {'description': '1 MERIDOL ZAHNBUERSTE  ', 'price': 2.85, 'vat': 'A'},
 {'description': '1 TEPE INTERDENTALB .  ', 'price': 4.35, 'vat': 'A'},
 {'description': '1 NIVEA HAIR C . SHAMP  ', 'price': 2.25, 'vat': 'A'}]

sum:
46.54

vats:
[{'brutto': 3.0, 'class': 'B', 'netto': 2.8, 'taxRate': 7.0},
 {'brutto': 43.54, 'class': 'A', 'netto': 36.59, 'taxRate': 19.0}]

vatSum:
{'brutto': 46.54, 'netto': 39.39}
```
