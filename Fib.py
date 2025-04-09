"""This file acts as the main module for this script."""

import traceback
import math
import sys

# Only import Fusion 360 modules if not in test mode
if 'test' not in sys.argv:
    import adsk.core
    import adsk.fusion
    # import adsk.cam

    # Initialize the global variables for the Application and UserInterface objects.
    app = adsk.core.Application.get()
    ui  = app.userInterface

    # Global variables to maintain references to event handlers
    handlers = []

class Point3D:
    """Simple Point3D class for testing without Fusion 360"""
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

def get_bounding_box(points):
    """Calculate the bounding box of a set of points."""
    if not points:
        return (0, 0, 0, 0)
    
    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)
    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)
    
    return (min_x, max_x, min_y, max_y)

def test_spiral_dimensions():
    """Test the spiral dimensions for various inputs."""
    test_cases = [
        (100, 100.0, 1.0, 0.0),   # 100 points, 100mm scale, 1 turn, 0mm height
        (200, 50.0, 2.0, 0.0),    # 200 points, 50mm scale, 2 turns, 0mm height
        (50, 200.0, 0.5, 0.0),    # 50 points, 200mm scale, 0.5 turns, 0mm height
        (100, 100.0, 1.0, 50.0),  # 100 points, 100mm scale, 1 turn, 50mm height
        (50, 100.0, 1.0, 25.0),   # 50 points, 100mm scale, 1 turn, 25mm height
    ]
    
    for num_points, scale, turns, height in test_cases:
        points = generate_fibonacci_points(num_points, scale, turns, height)
        min_x, max_x, min_y, max_y = get_bounding_box(points)
        
        width = max_x - min_x
        height_dim = max_y - min_y
        max_dimension = max(width, height_dim)
        
        # Allow 1% tolerance for floating point errors
        tolerance = scale * 0.01
        if abs(max_dimension - scale) > tolerance:
            print(f"Test failed for scale={scale}mm, turns={turns}, height={height}mm")
            print(f"Expected max dimension: {scale}mm")
            print(f"Actual max dimension: {max_dimension}mm")
            print(f"Bounding box: {width}mm x {height_dim}mm")
            return False
        
        # Test height if specified
        if height > 0:
            min_z = min(p.z for p in points)
            max_z = max(p.z for p in points)
            actual_height = max_z - min_z
            
            if abs(actual_height - height) > tolerance:
                print(f"Test failed for height={height}mm")
                print(f"Expected height: {height}mm")
                print(f"Actual height: {actual_height}mm")
                print(f"Z range: {min_z}mm to {max_z}mm")
                return False
    
    print("All tests passed!")
    return True

def generate_fibonacci_points(num_points: int, scale: float = 1.0, turns: float = 1.0, height: float = 0.0):
    """Generate points for a Fibonacci spiral."""
    points = []
    
    # Golden ratio
    phi = (1 + math.sqrt(5)) / 2
    
    # Angle increment for smooth spiral
    angle_increment = (2 * math.pi * turns) / num_points
    
    # First generate points without scaling to find the actual maximum extent
    unscaled_points = []
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')
    
    for i in range(num_points):
        angle = i * angle_increment
        radius = math.pow(phi, 2 * angle / math.pi)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        unscaled_points.append((x, y))
        
        # Track bounding box
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)
    
    # Calculate the maximum dimension of the unscaled spiral
    width = max_x - min_x
    height_dim = max_y - min_y
    max_dimension = max(width, height_dim)
    
    # Calculate scaling factor to match desired scale
    scaling_factor = scale / max_dimension
    
    # Calculate the Z increment per point
    z_increment = height / num_points if num_points > 0 else 0
    
    # Generate final scaled points with Z-coordinate ramping
    current_z = 0
    for x, y in unscaled_points:
        x_scaled = x * scaling_factor
        y_scaled = y * scaling_factor
        
        if 'test' in sys.argv:
            points.append(Point3D(x_scaled, y_scaled, current_z))
        else:
            points.append(adsk.core.Point3D.create(x_scaled, y_scaled, current_z))
        
        # Increment Z for next point
        current_z += z_increment
    
    return points

# Only define Fusion 360 specific classes and functions if not in test mode
if 'test' not in sys.argv:
    class FibonacciSpiralCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
        def __init__(self):
            super().__init__()
        
        def notify(self, args):
            try:
                cmd = args.command
                inputs = cmd.commandInputs
                
                # Create value input for number of points (unitless)
                num_points_input = inputs.addValueInput('num_points', 'Number of Points', '', adsk.core.ValueInput.createByReal(100))
                num_points_input.minimumValue = 10
                num_points_input.maximumValue = 1000
                
                # Create value input for scale
                scale_input = inputs.addValueInput('scale', 'Scale', 'mm', adsk.core.ValueInput.createByReal(100.0))
                scale_input.minimumValue = 0.1
                scale_input.maximumValue = 1000.0
                
                # Create value input for number of turns
                turns_input = inputs.addValueInput('turns', 'Number of Turns', '', adsk.core.ValueInput.createByReal(1.0))
                turns_input.minimumValue = 0.1
                turns_input.maximumValue = 10.0
                
                # Create value input for height
                height_input = inputs.addValueInput('height', 'Height', 'mm', adsk.core.ValueInput.createByReal(0.0))
                height_input.minimumValue = 0.0
                height_input.maximumValue = 1000.0
                
                # Create checkbox for using splines
                use_splines_input = inputs.addBoolValueInput('use_splines', 'Use Splines', True, '', True)
                
                # Connect to the execute event
                onExecute = FibonacciSpiralCommandExecuteHandler()
                cmd.execute.add(onExecute)
                handlers.append(onExecute)
                
                # Connect to the destroy event
                onDestroy = FibonacciSpiralCommandDestroyHandler()
                cmd.destroy.add(onDestroy)
                handlers.append(onDestroy)
                
            except:
                if ui:
                    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    class FibonacciSpiralCommandExecuteHandler(adsk.core.CommandEventHandler):
        def __init__(self):
            super().__init__()
        
        def notify(self, args):
            try:
                cmd = args.command
                inputs = cmd.commandInputs
                
                # Get the input values
                num_points = int(inputs.itemById('num_points').value)
                scale = inputs.itemById('scale').value
                turns = inputs.itemById('turns').value
                height = inputs.itemById('height').value
                use_splines = inputs.itemById('use_splines').value
                
                # Get the active document
                doc = app.activeDocument
                if not doc:
                    ui.messageBox('No active document')
                    return

                # Get the root component
                root = doc.design.rootComponent
                
                # Create a new sketch on the XY plane
                sketches = root.sketches
                xy_plane = root.xYConstructionPlane
                sketch = sketches.add(xy_plane)
                
                # Generate points for the Fibonacci spiral
                points = generate_fibonacci_points(num_points, scale, turns, height)
                
                if use_splines:
                    # Create a collection of points for the spline
                    point_collection = adsk.core.ObjectCollection.create()
                    for point in points:
                        point_collection.add(point)
                    
                    # Create a fitted spline through the points
                    sketch.sketchCurves.sketchFittedSplines.add(point_collection)
                else:
                    # Draw lines between consecutive points
                    for i in range(len(points) - 1):
                        sketch.sketchCurves.sketchLines.addByTwoPoints(points[i], points[i + 1])
                
                # Finish the sketch
                sketch.isComputeDeferred = False
                
            except:
                if ui:
                    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    class FibonacciSpiralCommandDestroyHandler(adsk.core.CommandEventHandler):
        def __init__(self):
            super().__init__()
        
        def notify(self, args):
            try:
                # When the command is done, terminate the script
                adsk.terminate()
            except:
                if ui:
                    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def run(_context: str):
        """This function is called by Fusion when the script is run."""
        try:
            # Get the command definitions
            cmd_defs = ui.commandDefinitions
            
            # Check if the command exists and delete it if it does
            cmd_def = cmd_defs.itemById('FibonacciSpiral')
            if cmd_def:
                cmd_def.deleteMe()
            
            # Create the command definition
            cmd_def = cmd_defs.addButtonDefinition(
                'FibonacciSpiral', 
                'Fibonacci Spiral', 
                'Creates a Fibonacci spiral using lines'
            )
            
            # Connect to the command created event
            onCommandCreated = FibonacciSpiralCommandCreatedHandler()
            cmd_def.commandCreated.add(onCommandCreated)
            handlers.append(onCommandCreated)
            
            # Execute the command
            cmd_def.execute()
            
            # Prevent this module from being terminated when the script returns
            adsk.autoTerminate(False)
            
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Run tests if script is run directly with 'test' argument
if __name__ == '__main__' and 'test' in sys.argv:
    test_spiral_dimensions()
