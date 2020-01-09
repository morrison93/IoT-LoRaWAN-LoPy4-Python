import os

try:
    print('deleting logs')
    for filename in os.listdir():
        if filename.endswith('.log'):
            print('deleting ' + filename)
            os.remove(filename)

except Exception as e:
    print('no log files to delete')
