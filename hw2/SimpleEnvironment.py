import numpy as np
import pylab as pl
import time
import copy

class SimpleEnvironment(object):
    def __init__(self, herb):
        self.robot = herb.robot
        self.boundary_limits = [[-5., -5.], [5., 5.]]

        # add an obstacle
        table = self.robot.GetEnv().ReadKinBodyXMLFile('models/objects/table.kinbody.xml')
        self.robot.GetEnv().Add(table)

        table_pose = np.array([[ 0, 0, -1, 1.0], 
                                  [-1, 0,  0, 0], 
                                  [ 0, 1,  0, 0], 
                                  [ 0, 0,  0, 1]])
        table.SetTransform(table_pose)

        # goal sampling probability
        self.p = 0.0

    def SetGoalParameters(self, goal_config, p = 0.2):
        self.goal_config = goal_config
        self.p = p

    #returns true if a point is not in collision
    def isValid(self, point):
        T = np.identity(4)
        T[0,3] = point[0]
        T[1,3] = point[1]
        self.robot.SetTransform(T)
        return not self.robot.GetEnv().CheckCollision(self.robot)

    
    def GenerateRandomConfiguration(self):
        config = np.random.random(2)
        limits = np.array(self.boundary_limits)
        config = (config * (limits[1] - limits[0])) + limits[0]
        return config if self.isValid(config) else self.GenerateRandomConfiguration()

    def ComputeDistance(self, start_config, end_config):
        dist = np.sqrt((start_config[0] - end_config[0])**2 + (start_config[1] - end_config[1])**2)
        return dist

    def Extend(self, start_config, end_config):
        configs = np.array([start_config, end_config])
        last = start_config
        for tau in np.arange(0.0, 1.01, 0.01):
            newconfig = np.average(configs, axis=0, weights=[1.0-tau, tau])
            if(self.isValid(newconfig)):
                last = newconfig
            else:
                break
        # return the last collision free point 
        return last

    def ComputePathLength(self, path):      
	i = 1
        length = 0.0
        while i < len(path):
            length += self.ComputeDistance(path[i-1], path[i])
            i += 1
        return length

    def ShortenPath(self, path, timeout=5.0):
        start = end = time.time()
        lastPath = []

        # stop when there's no more shortening to be done 
        while not np.array_equal(path, lastPath): 
            lastPath = copy.deepcopy(path)

            # keep checking alternate adjacent nodes  
            idx = 1
            while idx < (len(path) - 1):
                n1 = path[idx - 1] 
                n2 = path[idx + 1]

                if np.array_equal(self.Extend(n1, n2), n2):
                    #delete the selected node
                    path = np.delete(path, idx, axis = 0)
                idx += 1
            # break out of while loop when time out 
            if (time.time() - start) > timeout: break
        return path

    def InitializePlot(self, goal_config):
        self.fig = pl.figure()
        lower_limits, upper_limits = self.boundary_limits
        pl.xlim([lower_limits[0], upper_limits[0]])
        pl.ylim([lower_limits[1], upper_limits[1]])
        pl.plot(goal_config[0], goal_config[1], 'gx')

        # Show all obstacles in environment
        for b in self.robot.GetEnv().GetBodies():
            if b.GetName() == self.robot.GetName():
                continue
            bb = b.ComputeAABB()
            pl.plot([bb.pos()[0] - bb.extents()[0],
                     bb.pos()[0] + bb.extents()[0],
                     bb.pos()[0] + bb.extents()[0],
                     bb.pos()[0] - bb.extents()[0],
                     bb.pos()[0] - bb.extents()[0]],
                    [bb.pos()[1] - bb.extents()[1],
                     bb.pos()[1] - bb.extents()[1],
                     bb.pos()[1] + bb.extents()[1],
                     bb.pos()[1] + bb.extents()[1],
                     bb.pos()[1] - bb.extents()[1]], 'r')
                    
                     
        pl.ion()
        pl.show()
        
    def PlotEdge(self, sconfig, econfig):
        pl.plot([sconfig[0], econfig[0]],
                [sconfig[1], econfig[1]],
                'k.-', linewidth=2.5)
        pl.draw()

