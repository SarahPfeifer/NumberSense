import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import VisualModel from '../components/student/VisualModels';
import api from '../services/api';

export default function PracticeSession() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [problem, setProblem] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [textAnswer, setTextAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const startTimeRef = useRef(null);

  const loadNextProblem = useCallback(async (sid) => {
    const sessionId = sid || (session && session.id);
    if (!sessionId) return;
    try {
      const p = await api.getNextProblem(sessionId);
      setProblem(p);
      setFeedback(null);
      setSelectedAnswer('');
      setTextAnswer('');
      startTimeRef.current = Date.now();
    } catch (err) {
      if (err.message.includes('complete')) {
        navigate(`/student/complete/${sessionId}`);
      } else {
        setError(err.message);
      }
    }
  }, [session, navigate]);

  // Start session
  useEffect(() => {
    api.startSession(assignmentId)
      .then(s => {
        setSession(s);
        return api.getNextProblem(s.id);
      })
      .then(p => {
        setProblem(p);
        startTimeRef.current = Date.now();
      })
      .catch(err => setError(err.message));
  }, [assignmentId]);

  const handleSubmitAnswer = async (answer) => {
    if (submitting || !problem) return;
    const responseTime = Date.now() - startTimeRef.current;
    setSubmitting(true);
    setSelectedAnswer(answer);
    try {
      const fb = await api.submitAnswer({
        session_id: session.id,
        problem_id: problem.problem_id,
        student_answer: answer,
        response_time_ms: responseTime,
      });
      setFeedback(fb);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textAnswer.trim()) {
      handleSubmitAnswer(textAnswer.trim());
    }
  };

  const handleNext = () => {
    loadNextProblem();
  };

  if (error) {
    return (
      <>
        <Navbar />
        <div className="practice-container">
          <div className="practice-card">
            <p style={{ color: 'var(--ns-red-600)' }}>{error}</p>
            <button className="btn btn-primary mt-2" onClick={() => navigate('/student')}>Back to Home</button>
          </div>
        </div>
      </>
    );
  }

  if (!session || !problem) {
    return (
      <>
        <Navbar />
        <div className="practice-container">
          <div className="practice-card">
            <p className="text-muted">Getting your practice ready...</p>
          </div>
        </div>
      </>
    );
  }

  const sessionTotal = problem.session_total || 15;
  const progress = feedback?.session_progress || { total: sessionTotal, answered: problem.sequence_number - 1, correct: 0 };
  const progressPct = (progress.answered / progress.total) * 100;
  const pd = problem.problem_data;
  const hasChoices = pd.choices && pd.choices.length > 0;
  const isInputType = !hasChoices || pd.type === 'equivalent_fractions';
  const isIntegerOp = pd.type === 'integer_addition' || pd.type === 'integer_subtraction';
  const isFractionType = ['fraction_comparison', 'fraction_comparison_benchmark', 'equivalent_fractions'].includes(pd.type);
  const isEquivFrac = pd.type === 'equivalent_fractions';
  const visualLevel = problem.visual_support_level || 5;
  // Interactive visuals: integers always, fractions at medium scaffolding (level 3-2)
  const useInteractive = isIntegerOp || (isFractionType && visualLevel <= 3 && visualLevel >= 2);

  const groupNum = problem.group_number || 1;
  const totalGroups = problem.total_groups || 5;
  const groupSize = problem.group_size || 3;
  const posInGroup = ((problem.sequence_number - 1) % groupSize) + 1;

  return (
    <>
      <Navbar />
      <div className="practice-container">
        {/* Group progress dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 8 }}>
          {Array.from({ length: totalGroups }, (_, i) => (
            <div key={i} style={{
              width: i + 1 === groupNum ? 28 : 18,
              height: 6,
              borderRadius: 3,
              background: i + 1 < groupNum ? 'var(--ns-indigo-500)'
                : i + 1 === groupNum ? 'var(--ns-indigo-600)'
                : 'var(--ns-gray-200)',
              transition: 'all 0.3s',
            }} />
          ))}
        </div>
        {/* Progress Bar */}
        <div className="progress-bar-wrapper">
          <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="flex-between text-sm text-muted" style={{ marginBottom: '1rem' }}>
          <span>Set {groupNum} of {totalGroups} &middot; Question {posInGroup} of {groupSize}</span>
          <span>{problem.sequence_number} / {sessionTotal}</span>
        </div>

        <div className="practice-card">
          {/* Prompt */}
          <div className="practice-prompt">{pd.prompt}</div>

          {/* Visual Model (if supports enabled) — visual scaffolding only, never auto-fills answer */}
          {problem.show_visual_support && pd.visual_hint && !feedback && (
            <VisualModel
              hint={pd.visual_hint}
              problemData={pd}
              interactive={useInteractive}
              visualLevel={visualLevel}
            />
          )}

          {/* Answer Area */}
          {!feedback && (
            <>
              {isInputType && pd.type === 'equivalent_fractions' ? (
                <form onSubmit={handleTextSubmit} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                  <input
                    className="answer-input"
                    type="text"
                    value={textAnswer}
                    onChange={e => setTextAnswer(e.target.value)}
                    placeholder="?"
                    autoFocus
                    disabled={submitting}
                  />
                  <button className="btn btn-primary" type="submit" disabled={!textAnswer.trim() || submitting}>
                    Submit
                  </button>
                </form>
              ) : hasChoices ? (
                <div className="practice-choices">
                  {pd.choices.map((choice, i) => (
                    <button
                      key={i}
                      className={`choice-btn ${selectedAnswer === choice ? 'selected' : ''}`}
                      onClick={() => handleSubmitAnswer(choice)}
                      disabled={submitting}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
              ) : (
                <form onSubmit={handleTextSubmit} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                  <input
                    className="answer-input"
                    type="text"
                    value={textAnswer}
                    onChange={e => setTextAnswer(e.target.value)}
                    placeholder="Type your answer"
                    autoFocus
                    disabled={submitting}
                  />
                  <button className="btn btn-primary" type="submit" disabled={!textAnswer.trim() || submitting}>
                    Submit
                  </button>
                </form>
              )}
            </>
          )}

          {/* Feedback */}
          {feedback && (
            <>
              <div className={`feedback-box ${feedback.is_correct ? 'feedback-correct' : 'feedback-incorrect'}`}>
                {feedback.is_correct ? (
                  <strong>{feedback.feedback?.encouragement || "That's right!"}</strong>
                ) : (
                  <>
                    <strong>{feedback.feedback?.correction}</strong>
                    <div style={{ marginTop: '.25rem' }}>
                      {feedback.feedback?.explanation}
                    </div>
                  </>
                )}
              </div>

              {/* Show visual model on incorrect answers — full static mode showing correct answer */}
              {!feedback.is_correct && feedback.feedback?.visual_hint && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.8125rem', color: '#6B7280', textAlign: 'center', marginBottom: 4, fontWeight: 600 }}>
                    Here's what the correct answer looks like:
                  </div>
                  <VisualModel hint={feedback.feedback.visual_hint} problemData={pd} interactive={false} visualLevel={5} />
                </div>
              )}

              {/* Choice highlights */}
              {hasChoices && (
                <div className="practice-choices mt-2">
                  {pd.choices.map((choice, i) => {
                    let cls = 'choice-btn';
                    if (choice === feedback.correct_answer) cls += ' correct';
                    else if (choice === selectedAnswer && !feedback.is_correct) cls += ' incorrect';
                    return (
                      <button key={i} className={cls} disabled style={{ cursor: 'default' }}>
                        {choice}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Adaptation notice between groups */}
              {feedback.adaptation_reason && (
                <div style={{
                  marginTop: '0.75rem', padding: '0.5rem 0.75rem',
                  background: 'var(--ns-indigo-50)', borderRadius: 'var(--ns-radius)',
                  fontSize: '0.8125rem', color: 'var(--ns-indigo-700)', textAlign: 'center',
                }}>
                  Adjusting for next set&hellip;
                </div>
              )}

              {feedback.session_progress.remaining === 0 ? (
                <button className="btn btn-primary btn-lg mt-2"
                  onClick={() => navigate(`/student/complete/${session.id}`)}
                  style={{ minWidth: 160 }}>
                  See Results
                </button>
              ) : (
                <button className="btn btn-primary btn-lg mt-2" onClick={handleNext} style={{ minWidth: 160 }}>
                  Next
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
