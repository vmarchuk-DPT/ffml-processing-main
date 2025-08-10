

def is_evil(result):

	# Only evaluate bipartite questions.
	if result.question.type != 'bipartite_choice' and result.question.type != 'tripartite_choice':
		return False

	# Only evaluate mouse paths (not touchscreens).
	if not len(result.path) > 10:
		return False

	# Heuristic for straight line.
	if result.features['diverge']['maxDivergence'][0] > 0.1:
		return False

	if result.question.duration > 2000:
		return False

	return True
