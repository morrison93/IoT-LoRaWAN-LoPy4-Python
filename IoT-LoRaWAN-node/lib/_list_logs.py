import os

try:
    print('listing logs')
    for filename in os.listdir():
        if filename.endswith('.log'):
            print(filename)


except Exception as e:
    print('no log files to delete')
