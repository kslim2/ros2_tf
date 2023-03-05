#!usr/bin/env python3

import math 
import rclpy 
from rclpy.node import Node 
import tf_transformations
from tf2_ros import TransformException 
from tf2_ros.buffer import Buffer 
from tf2_ros.transform_listener import TransformListener 
from geometry_msgs.msg import Twist 
from turtlesim.srv import Spawn 


class TurtleFollowing(Node):

    def __init__(self, name):
        super().__init__(name)
        
        self.declare_parameter("source_frame", "turtle1")
        self.source_frame = self.get_parameter("source_frame")\
            .get_parameter_value().string_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.spawner = self.create_client(Spawn, "spawn")
        self.turtle_spawning_service_ready = False 
        self.turtle_spawned = False 

        self.publisher = self.create_publisher(Twist, "turtle2/cmd_vel", 1)

        self.timer = self.create_timer(1.0, self.on_timer)

    def on_timer(self):
        from_frame_rel = self.source_frame 
        to_frame_rel = "turtle2" 

        if self.turtle_spawning_service_ready:
            if self.turtle_spawned:
                try:
                    now = rclpy.time.Time()
                    trans = self.tf_buffer.lookup_transform(
                        to_frame_rel,
                        from_frame_rel,
                        now 
                    )
                except TransformException as ex:
                    self.get_logger().info(
                        f"Could not transform {to_frame_rel} to {from_frame_rel}: {ex}"
                    )
                    return 

                msg = Twist()
                scale_rotation_rate = 1.0 
                msg.angular.z = scale_rotation_rate * math.atan2(
                    trans.transform.translation.y, 
                    trans.transform.translation.x 
                )
                scale_forward_speed = 0.5 
                msg.linear.x = scale_forward_speed * math.sqrt(
                    trans.transform.translation.x ** 2 + 
                    trans.transform.translation.y ** 2 
                )

                self.publisher.publish(msg )
            else:
                if self.result_done():
                    self.get_logger().info(
                        f"Successfully spawned {self.result.result().name}"
                    )
                    self.turtle_spawned = True 
                else:
                    self.get_logger().info("Spawn is not finished")

        else:
            if self.spawner.service_is_ready():
                request = Spawn.Request()
                request.name = "turtle2"
                request.x = float(4)
                request.y = float(2)
                request.theta = float(0)

                self.result = self.spawner.call_async(request)
                self.turtle_spawning_service_ready = True 
            else:
                self.get_logger().info("Service is not ready")

def main(args=None):

    rclpy.init(args=args)
    node = TurtleFollowing("turtle_following")
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()