resource "aws_db_instance" "booklocal" {
  identifier             = "booklocal-db-tf"
  engine                 = "postgres"
  engine_version         = "16.15"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "booklocal"
  username               = "booklocal"
  password               = var.db_password
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true
  skip_final_snapshot    = true
}
