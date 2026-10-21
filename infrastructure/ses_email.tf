# Role the running container uses to call AWS. It can only send email via SES.
resource "aws_iam_role" "ecs_task" {
  name = "booklocal-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_send_email" {
  name = "send-email-via-ses"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ses:SendEmail", "ses:SendRawEmail"]
      Resource = "arn:aws:ses:eu-west-1:325774504679:identity/*"
    }]
  })
}

output "ecs_task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}
