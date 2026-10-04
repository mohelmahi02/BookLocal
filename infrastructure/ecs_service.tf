data "aws_ecs_cluster" "booklocal" {
  cluster_name = "booklocal-cluster"
}

data "aws_ecs_task_definition" "booklocal" {
  task_definition = "booklocal-backend"
}

resource "aws_ecs_service" "booklocal" {
  name            = "booklocal-service"
  cluster         = data.aws_ecs_cluster.booklocal.arn
  task_definition = data.aws_ecs_task_definition.booklocal.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      "subnet-0bb246fd25c873872",
      "subnet-02d90638512d9fb42",
      "subnet-0ec269f2bec9c92bf"
    ]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "booklocal-backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.backend]

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}
