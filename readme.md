Librarius
===
The Software for assist your transcription of handwritten documents.


## Define enviroment
You need to have the anaconda environment manager installed on your computer.
If so, run the command
```console
conda env create -f environment.yml
```
and acrivate the enviroment: 
```console
conda activate librarius
```


## Preparation
1. Create a ```"data"``` folder which contains three subfolders:
   
   1.1 `alignments` - here you need to put the `.asl` files
   
   1.2 `doc_img` - here you need to put the doc images
   
   1.3 `line_segmentation` - here you neet to put the line segmentation files


## Run the application
To run the application you can use the command
```console
python GUI.py
```
