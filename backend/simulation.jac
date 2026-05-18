// Jac-facing simulation sketch for the hackathon pitch.
// The runnable MVP mirrors these flows in backend/app/simulation.py.

walker Agent {
  has hunger: int;
  has health: int;
  has goal: str;

  can choose_goal with World entry {
    if self.hunger > 80 {
      self.goal = "find_food";
    } elif here.has_disaster {
      self.goal = "avoid_disaster";
    } else {
      self.goal = "explore";
    }
  }
}

node World {
  has tick: int;
  has resources: list;
  has events: list;
}

