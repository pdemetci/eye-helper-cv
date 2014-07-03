import cv2 
import numpy as np 
import csv

def labelData(basename, startframe, endframe, savepath):
    """Takes in the video and the section where the object is visible
    allows the user to create a box around the ojbect being tracked. The 
    corners of this box are saved as the position of the object

    ***Assumes that the input will be a jpg file
    ***endframe is inclusive (eg. if you choose 2 you will end on frame 2
        not on frame 1)
    ***Assumes use of linux in way filepaths are defined
    """
    c1 = (0,0)
    c2 = (20,20)
    #creates a new csv file to store data
    with open(savepath + '/' + basename+".csv", "w") as csvfile:
        keypointwriter = csv.writer(csvfile, delimiter= ',',
                               quotechar='|', quoting=csv.QUOTE_MINIMAL)           
        for i in range(startframe, endframe + 1):
            #names start w/ 4 '0's below makes correct number to add to basename
            frame = (4 -len(str(i))) * '0' + str(i)         
            while(1):
                #draws rectangle over image resizing/ translating from user imnput
                temp = cv2.imread(basename + frame +'.jpg')
                k = cv2.waitKey(5)
                cv2.rectangle(temp,c1, c2, (0, 0, 255),2) 
                cv2.imshow('rec', temp)
                if k == ord('s'):
                    c1 = (c1[0], c1[1]+5)
                elif k == ord('d'):
                    c1 = (c1[0]+5, c1[1])
                elif k == ord('a'):
                    c1= (c1[0]-5, c1[1])
                elif k == ord('w'):
                    c1= (c1[0], c1[1]-5)
                elif k == 65363:        #Right
                    c1 = (c1[0]+5, c1[1])
                    c2 = (c2[0]+5, c2[1])
                elif k == 65361:        #Left
                    c1 = (c1[0]-5, c1[1])
                    c2 = (c2[0]-5, c2[1])
                elif k == 65364:        #up
                    c1 = (c1[0], c1[1]+5)
                    c2 = (c2[0], c2[1]+5)
                elif k == 65362:        #down
                    c1 = (c1[0], c1[1]-5)
                    c2 = (c2[0], c2[1]-5)

                elif k == 32:
                    break

            keypointwriter.writerow([frame, c1[0], c1[1], c2[0], c2[1]])

if __name__ == '__main__':
    labelData()
