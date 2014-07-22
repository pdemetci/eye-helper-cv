import cv2
import numpy as np 
import csv
import pickle
import scipy 
import os
import math
from objectmatch import mean_shift
import matplotlib.pyplot as plt  
from plotdata import plot
import pprint as pp

def calc_center(g_truth):
    """ 
        Function finds the center of a box

        Inputs: g_truth -> four corners of a box
        Returns: center -> the center of the box
    """

    x = int((g_truth[2]+g_truth[0])/2)
    y = int((g_truth[3]+g_truth[1])/2)
    return x, y

def superdata(q_pickle, t_pickle, q_gtruth, t_gtruth, frame, method, t_img):
    """
        we may or may not rename this function in the near future to be something more descriptive... 
        --emily and lindsey, july 18, 2014

        Inputs:
            q_pickle -> keypoint and descriptor data from query image
            t_pickle -> keypoint and descriptor data from training image
            g_truth -> coordinates of labeled box around actual object
            frame -> frame number
            method -> kp detector method used to get points
            t_img -> training image frame number

        We assume that the object has been perfectly selecdted so we use ground truth values for the training image region.

        Returns:
            c_center -> center of the object tracking circle
            b_center -> center of the object
            match -> boolean True or False
            frame -> the number of the frame
            t_frame -> number of the training image
            kp_matches -> total number of matched keypoints
            c_matches -> number of correctly matched keypoints
    """
    #load query image data
    q = pickle.load(open(q_pickle, 'rb'))
    q_k = q[0]
    q_d = q[1]

    #load training image data
    t = pickle.load(open(t_pickle, 'rb'))
    t_k = t[0]
    t_d = t[1]

    #iterate through the training keypoints and only keep those that are within the selected object
    #In this case we are using the training image's ground truth as the selection
    train_d = []
    train_k =[]
    for index in range(len(t_k)):
        if t_gtruth[2]<=t_k[index][0]<=t_gtruth[0] and t_gtruth[3]<=t_k[index][1]<=t_gtruth[1]:
            train_d.append(t_d[index])
            train_k.append(t_k[index])
    t_k = train_k
    t_d = np.array(train_d)

    #Selects the correct matcher parameters depending on the keypoint detector used
    if method == 'SIFT' or method == 'SURF':
        bf = cv2.BFMatcher()
    else: #for ORB or BRISK
        bf = cv2.BFMatcher(normType = cv2.NORM_HAMMING)

    try:
        #matches keypoints of *training* image to query, not other way around
        matches = bf.knnMatch(t_d, q_d, k=2)

        good_matches = []
        #goes through and only keeps matches passing a nearest neighbor test to reduce false matches
        for m,n in matches:
            if m.distance < 0.75*n.distance:
                # Get coordinate of the match
                m_x = int(q_k[m.trainIdx][0])
                m_y = int(q_k[m.trainIdx][1])
                good_matches.append((m_x, m_y))

        #uses mean_shift to find the object from the keypoints detected
        c_center, radius = mean_shift(hypothesis = (100, 100), keypoints = good_matches, threshold = 10, frame = frame)
        b_center = calc_center(q_gtruth)
        
        #checking each keypoint in good_matches
        kp_matches = len(good_matches)
        c_matches = 0
        for match in good_matches:
            if q_gtruth[2]<=match[0]<=q_gtruth[0] and q_gtruth[3]<=match[1]<=q_gtruth[1]:
                c_matches +=1
    
        #checking if the center is within the labeled query box
        if q_gtruth[2]<=c_center<=q_gtruth[0] and q_gtruth[3]<=c_center<=q_gtruth[1]:
            match = True
        else:
            match = False

        # distance from center 
        d_from_c = math.hypot(c_center[0]-b_center[0], c_center[1]-b_center[1])
        # return c_center, b_center, d_from_c, match, frame, t_img, kp_matches, c_matches
        return {'c_center': c_center, 'b_center': b_center, 'd_from_c': d_from_c,'match': match, 'frame': frame, 't_img': t_img, 'kp_matches': kp_matches, 'c_matches': c_matches}
   
    except:
        print "Likely there are no good matches..."
        return None


def plot_superdata(plottables, mstr):

    # g_truth = plottables['boxes']
    # print g_truth

    # #Getting box coordinates for now... eventually this'll go into gen_plottables
    # for line in reversed(open('./gstore-csv/%s.csv' % 'cookie').readlines()):
    #     row = line.rstrip().split(',')
    #     g_truth[int(row[0])] = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]

    # pp.pprint(g_truth)

    for trial in plottables:
        if trial not in [144, 164, 284]: #we don't want to plot these
            trialdata = plottables[trial]

            #Getting temporal frame distance from training image instead of franem number from filename
            frames = [int(x) - trial for x in trialdata['frame numbers']]

            #setting up kp variables to plot
            total_kp = trialdata['total kp matches']
            correct_kp = [ trialdata['correct kp matches'][x]/float(trialdata['total kp matches'][x]) * 100 for x in range(len(frames))]

            # Normalizing d_from_c values (to account for the size of the item changing as the video progresses)
            d_from_c = [trialdata['distance from center'][x]/trialdata['hypotenuse'][x] for x in range(len(trialdata['distance from center']))]           

            #frame number (or frames since training image) vs distance from center of object
            plt.subplot(3,1,1)
            plt.plot(frames, d_from_c, 'o', label=trial)
            plt.ylabel('distance from center of object')
            plt.xlabel('# of frames since training image')
            plt.title('cookie %s distance from center vs frames for various training images (normalized)' % mstr)
            plt.legend()

            #start frame in sequence vs. overall accuracy of sequence
            #overall accuracy to be done when we have more method data

            #frame number (or frames since training image) vs. total keypoint matches
            plt.subplot(3,1,2)
            plt.plot(frames, total_kp, 'o', label=trial)
            plt.ylabel('total keypoints for each frame')
            plt.xlabel('# of frames since training image')
            plt.title('cookie %s total keypoints for each frame vs frames for various training images' % mstr)
            plt.legend()

            #frame number (or frames since training image) vs. correct keypoint matches/len(frames)
            plt.subplot(3,1,3)
            plt.plot(frames, correct_kp, 'o', label=trial)
            plt.ylabel('percent correct keypoints for each frame')
            plt.xlabel('# of frames since training image')
            plt.title('cookie %s percent correct keypoints for each frame vs frames for various training images' % mstr)
            plt.legend()

    plt.show()
    # plt.savefig("./OT-res/compare_kpd_plots/cookie_%s_d_from_c_all.png" % mstr)

def gen_plottables(methods, dataset, framerange):
    #plot-friendly data structure
    #{key = training image number : value = {frame numbers: [], boxes: {}, overall accuracy: [], :distance from center: [], total kp matches: [], correct kp matches: []}}
    plottables = {}

    # cookie sift (for the entire cookie video)
    framestart = framerange[0]
    framemax = framerange[1]
    
    for m in methods:
        t_img_number = framestart 
        while t_img_number < 140:# framemax:
            print m
            print t_img_number
            #instantiating plottables for this training image trial
            plottables[t_img_number] = {'frame numbers': [],
                                        'boxes': {}, 
                                        'hypotenuse': [],
                                        'overall accuracy': 0, 
                                        'distance from center': [], 
                                        'total kp matches': [], 
                                        'correct kp matches': []}

            ################ start of a t_img trial
            for line in reversed(open('./gstore-csv/%s.csv' % dataset).readlines()):
                row = line.rstrip().split(',')
                print row
                plottables[t_img_number]['boxes'][int(row[0])] = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]

                #training image is never a "future frame"
                #for example, if the training image is frame 144, the test starts from frame 144, not frame 124

                if int(row[0]) == t_img_number:
                    q_img_number = int(row[0])
                    plottables[t_img_number]['frame numbers'].append(row[0])
                    t_gtruth = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]
                    q_gtruth = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]
                    data = superdata(q_pickle = './OT-res/kp_pickles/%s/%s/%s_00%d_keypoints.p' % (dataset, m, dataset, q_img_number), 
                        t_pickle = './OT-res/kp_pickles/%s/%s/%s_00%d_keypoints.p' % (dataset, m, dataset, t_img_number), 
                        q_gtruth = q_gtruth,
                        t_gtruth = t_gtruth, 
                        frame = q_img_number, 
                        method = m, 
                        t_img = t_img_number)    
                    if data != None:        
                        hypotenuse = math.sqrt((q_gtruth[0]-q_gtruth[2])**2 + (q_gtruth[1]-q_gtruth[3])**2)
                        plottables[t_img_number]['hypotenuse'].append(hypotenuse)
                        plottables[t_img_number]['distance from center'].append(data['d_from_c'])
                        plottables[t_img_number]['total kp matches'].append(data['kp_matches'])
                        plottables[t_img_number]['correct kp matches'].append(data['c_matches'])

                elif int(row[0]) > t_img_number:
                    q_img_number = int(row[0])
                    q_gtruth = [int(row[1]), int(row[2]), int(row[3]), int(row[4])]
                    data = superdata(q_pickle = './OT-res/kp_pickles/%s/%s/%s_00%d_keypoints.p' % (dataset, m, dataset, q_img_number), 
                                    t_pickle = './OT-res/kp_pickles/%s/%s/%s_00%d_keypoints.p' % (dataset, m, dataset, t_img_number), 
                                    q_gtruth = q_gtruth,
                                    t_gtruth = t_gtruth, 
                                    frame = q_img_number, 
                                    method = m, 
                                    t_img = t_img_number)
                    if data != None:
                        hypotenuse = math.sqrt((q_gtruth[0]-q_gtruth[2])**2 + (q_gtruth[1]-q_gtruth[3])**2)
                        plottables[t_img_number]['hypotenuse'].append(hypotenuse)
                        plottables[t_img_number]['frame numbers'].append(row[0])
                        plottables[t_img_number]['distance from center'].append(data['d_from_c'])
                        plottables[t_img_number]['total kp matches'].append(data['kp_matches'])
                        plottables[t_img_number]['correct kp matches'].append(data['c_matches'])

            try:
                plottables[t_img_number]['overall accuracy'] = ( float(sum(plottables[t_img_number]['correct kp matches'])) / sum(plottables[t_img_number]['total kp matches']) ) * 100
            except:
                plottables[t_img_number]['overall accuracy'] = 0
            ################ end of a t_img trial
            t_img_number += 20 #try a different training image (every 20 frames)... from frame 124 to 288 for cookie
        pickle.dump(plottables, open('./OT-res/compare_kpd_plots/%s_%s.p' % (dataset, m), 'wb'))            


if __name__ == '__main__':

    #loops for datasets, methods, t_img while, q_imgs

    # # methods = ['ORB', 'SIFT', 'BRISK', 'SURF']
    # methods = ['SIFT']
    # plottables = gen_plottables(methods, 'cookie', [124, 288])
    # pp.pprint(plottables)
    # plot_superdata(plottables, 'SIFT')

    for mstr in ['SIFT']:
        data = pickle.load(open('./OT-res/compare_kpd_plots/%s_%s.p' % ('cookie', mstr), 'rb'))
        pp.pprint(data)
        plot_superdata(data, mstr)

    ### notes:
    #normalize things
    #maybe it's a blurry section of the video (meanshift can be dramatic)
    #plotting precision too
    #tuning meanshift? combining methods?
