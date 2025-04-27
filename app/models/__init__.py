# Để đảm bảo mô hình được nhập đúng trình tự
from app.models.user import User
from app.models.learning import (
    Level, Lesson, UserProgress, PronunciationExercise, 
    PronunciationAttempt, Vocabulary, Test, SampleSentence
)
from app.models.chat import ChatRoom, RoomParticipant, Message, StatusPost, Comment 

# Import models để các module khác có thể import từ app.models
from app.models.models import * 