import click
from flask.cli import with_appcontext
from flask import current_app
from models.models import User, db

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create a new admin user.
    
    Example:
        flask create-admin admin admin@example.com password123
    """
    try:
        if User.query.filter_by(username=username).first():
            click.echo(f"Error: Username {username} already exists.")
            return
        if User.query.filter_by(email=email).first():
            click.echo(f"Error: Email {email} already exists.")
            return
        
        user = User.create_admin(username, email, password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin user {username} created successfully.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin user: {str(e)}")

@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users in the system."""
    try:
        users = User.query.all()
        if not users:
            click.echo("No users found.")
            return
            
        click.echo("\nUser List:")
        click.echo("=" * 80)
        click.echo(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
        click.echo("-" * 80)
        
        for user in users:
            created = "N/A"  # User model hiện không có trường created_at
            click.echo(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {created}")
            
    except Exception as e:
        click.echo(f"Error listing users: {str(e)}")

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with required tables."""
    try:
        db.create_all()
        click.echo("Database tables created successfully.")
    except Exception as e:
        click.echo(f"Error creating database tables: {str(e)}")

def register_commands(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(init_db_command)
