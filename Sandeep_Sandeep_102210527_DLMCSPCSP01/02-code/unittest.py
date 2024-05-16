import unittest
from main import app, db, User, Task, datetime

class TestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_task_creation(self):
        """Test task creation functionality"""
        user = User(username='testuser', first_name='Test', last_name='User', email='test@example.com')
        user.set_password('securepassword')
        db.session.add(user)
        db.session.commit()
        self.app.post('/login', data=dict(username='testuser', password='securepassword'))
        response = self.app.post('/submit-new-task', data=dict(task_name='New Task', task_description='Test Description', task_date='2022-12-31'))
        self.assertIn(b'Task added successfully!', response.data)

    def test_task_deletion(self):
        """Test task deletion functionality"""
        user = User(username='testuser', first_name='Test', last_name='User', email='test@example.com')
        user.set_password('securepassword')
        db.session.add(user)
        db.session.commit()
        task = Task(name='Delete Task', description='Task to be deleted', due_date=datetime.utcnow(), user_id=user.id)
        db.session.add(task)
        db.session.commit()
        self.app.post('/login', data=dict(username='testuser', password='securepassword'))
        response = self.app.get(f'/delete_task/{task.id}')
        self.assertIn(b'Task removed successfully!', response.data)

if __name__ == '__main__':
    unittest.main()
