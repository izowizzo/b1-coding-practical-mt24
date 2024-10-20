from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from terrain import generate_reference_and_limits

class Submarine:
    def __init__(self):
        """Initialise the values associated with the submarine, including the initial position and velocities"""

        self.mass = 1
        self.drag = 0.1
        self.actuator_gain = 1

        self.dt = 1 # Time step for discrete time simulation

        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 1 # Constant velocity in x direction
        self.vel_y = 0


    def transition(self, action: float, disturbance: float):
        """Updates the position and velocity in the y direction using the control action outputted 
        from the controller function"""
        self.pos_x += self.vel_x * self.dt
        self.pos_y += self.vel_y * self.dt

        force_y = -self.drag * self.vel_y + self.actuator_gain * (action + disturbance)
        acc_y = force_y / self.mass
        self.vel_y += acc_y * self.dt
    
    def get_depth(self) -> float:
        """Returns the y position of submarine as a float"""
        return self.pos_y
    
    def get_position(self) -> tuple:
        """Returns the x position and y position of submarine as a tuple"""
        return self.pos_x, self.pos_y
    
    def reset_state(self):
        """Resets the velocities and positions of the submarine to their inital values"""
        self.pos_x = 0
        self.pos_y = 0
        self.vel_x = 1
        self.vel_y = 0
    
class Trajectory:
    def __init__(self, position: np.ndarray):
        """Stores the position in the self structure"""
        self.position = position  
        
    def plot(self):
        """plots the y position vs the x position of the positions stored in self"""
        plt.plot(self.position[:, 0], self.position[:, 1])
        plt.show()

    def plot_completed_mission(self, mission: Mission):
        """Interpolates the x coordinates at regular time intervals. Then plots this against the reference 
        values from the missions and the position of the submarine (stored in self). Plot then shows the 
        difference between the trajectory and the reference"""
        x_values = np.arange(len(mission.reference))
        min_depth = np.min(mission.cave_depth)
        max_height = np.max(mission.cave_height)

        plt.fill_between(x_values, mission.cave_height, mission.cave_depth, color='blue', alpha=0.3)
        plt.fill_between(x_values, mission.cave_depth, min_depth*np.ones(len(x_values)), 
                         color='saddlebrown', alpha=0.3)
        plt.fill_between(x_values, max_height*np.ones(len(x_values)), mission.cave_height, 
                         color='saddlebrown', alpha=0.3)
        plt.plot(self.position[:, 0], self.position[:, 1], label='Trajectory')
        plt.plot(mission.reference, 'r', linestyle='--', label='Reference')
        plt.legend(loc='upper right')
        plt.show()

@dataclass
class Mission:
    
    reference: np.ndarray
    cave_height: np.ndarray
    cave_depth: np.ndarray

    @classmethod
    def random_mission(cls, duration: int, scale: float):
        """Randomly generates data to pass through the controller"""
        (reference, cave_height, cave_depth) = generate_reference_and_limits(duration, scale)
        return cls(reference, cave_height, cave_depth)

    @classmethod
    def from_csv(cls, file_name: str):
        """Imports data from a csv file to be passed into the controller"""
        # You are required to implement this method
        import pandas as pd
        df = pd.read_csv(file_name)
        array = df.to_numpy()
        (reference, cave_height, cave_depth) = (array[:,0], array[:,1], array[:,2])
        return cls(reference, cave_height, cave_depth)
        
class Control:
    def __init__(self):
        """Initialises values required to pass through the controller"""
        self.Kp = 0.15
        self.Kd = 0.6
        self.previous_error = 0.0

    def controller(self, t, mission: Mission, observation_t):
        """Takes the y position at time t, before calculating current error. Calculates the control action
        and returns it as well as updating the previous_error."""

        self.current_error = mission.reference[t] - observation_t
        u_t = self.Kp*self.current_error + self.Kd*(self.current_error - self.previous_error)
        self.previous_error = self.current_error
        return u_t

class ClosedLoop:
    def __init__(self, plant: Submarine, controller: Control):
        self.plant = plant
        self.controller = controller

    def simulate(self,  mission: Mission, disturbances: np.ndarray) -> Trajectory:
        """Simulates the mission by finding the y position at time t and storing it in the 
        positions array. """
        T = len(mission.reference)
        if len(disturbances) < T:
            raise ValueError("Disturbances must be at least as long as mission duration")
        
        positions = np.zeros((T, 2))
        actions = np.zeros(T)
        self.plant.reset_state()

        for t in range(T):
            positions[t] = self.plant.get_position()
            observation_t = self.plant.get_depth()
            # surely observation_t is the previous output?
            # Call your controller here
            (actions[t]) = self.controller.controller(t, mission, observation_t)
            # Update the output as well as the action
            self.plant.transition(actions[t], disturbances[t])

        return Trajectory(positions)
        
    def simulate_with_random_disturbances(self, mission: Mission, variance: float = 0.5) -> Trajectory:
        """Passes random disturbances and mission into the simulate to find the Trajectory"""
        disturbances = np.random.normal(0, variance, len(mission.reference))
        return self.simulate(mission, disturbances)

#Testing my controller
sub = Submarine()
controller = Control()
closed_loop = ClosedLoop(sub, controller)

mission = Mission.from_csv('data/mission.csv')
print(mission)

trajectory = closed_loop.simulate_with_random_disturbances(mission)
trajectory.plot_completed_mission(mission)



