'''
This is the streaming version of the problem. We will use a heap to find the 10 largest files. 
We do have to helper API to help us to get the size of the file and its subdirectories. We will use the os.path.getsize() function to get the size of the file. And os.path.join() function to get the path of the file.
These are gonna be URIs.
These are gonna be going to be the children of the current directory.
Given a directory path, find the 10 largest files in the directory and its subdirectories.
'''
import os

def find_largest_files(directory: str) -> list[str]:
    max_heap = []
    files = os.listdir(directory)
    print(files)
    print('--------------------------------')
    for file in files:
        if os.path.isfile(file):
            max_heap.append(os.path.getsize(file))
        else:
            max_heap.append(find_largest_files(file))
    return max_heap

print(find_largest_files('/Users/jason/Desktop/test'))