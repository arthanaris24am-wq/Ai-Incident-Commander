from app.services.safety_gate import SafetyGate

class SolutionEngine:
    def __init__(self):
        self.safety_gate = SafetyGate()

    def select_best_solution(self, ai_response: dict) -> dict:
        """
        Takes the AI response and its multiple solutions, ranks them by:
        1. SafetyGate validity
        2. Risk Level (LOW > MEDIUM > HIGH)
        3. Confidence / Success Probability
        """
        solutions = ai_response.get("solutions", [])
        if not solutions:
            return None
            
        valid_solutions = []
        for sol in solutions:
            action = sol.get("action", "NONE").upper()
            target = sol.get("target", "")
            
            # Use safety gate to validate if action + target is permitted at all
            is_valid = self.safety_gate.validate_action(action, target)
            if is_valid:
                valid_solutions.append(sol)
                
        if not valid_solutions:
            return None

        # Sort solutions by risk level (LOW -> MEDIUM -> HIGH) and success probability
        risk_weights = {"LOW": 3, "MEDIUM": 2, "HIGH": 1}
        
        valid_solutions.sort(key=lambda s: (
            risk_weights.get(s.get("risk_level", "HIGH").upper(), 0),
            s.get("success_probability", 0)
        ), reverse=True)
        
        # Best valid solution
        return valid_solutions[0]
        
    def check_automation_allowance(self, solution: dict, confidence: float) -> bool:
        """
        Determines if a solution can be automatically executed without user approval.
        """
        if not solution:
            return False
            
        risk = solution.get("risk_level", "HIGH").upper()
        prob = solution.get("success_probability", 0)
        
        # Must not require approval explicitly
        if solution.get("requires_approval", True):
            return False
            
        # Hard limits
        if risk != "LOW":
            return False
            
        # Confidence thresholds
        if confidence >= 0.90 and prob >= 0.8:
            return True
            
        return False
