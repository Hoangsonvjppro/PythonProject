# Để đảm bảo mô hình được nhập đúng trình tự
from app.models.user import User
from app.models.learning import (
    Level, Lesson, UserProgress, PronunciationExercise, 
    PronunciationAttempt, Vocabulary, Test, SampleSentence
)
from app.models.chat import ChatRoom, RoomParticipant, Message, StatusPost, Comment 