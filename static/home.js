import React from "react";
import ReactDOM from "react-dom/client";
import * as NBAIcons from "react-nba-logos";

const HomePage = () => {
  const season = window.season;
  const teams = window.teams;

  const handleClick = (abbr) => {
    window.location.href = `/team/${abbr}?season=${season}`;
  };

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "32px",
      justifyContent: "center",
      alignItems: "center"
    }}>
      {teams.map((team) => {
        const Abbr = team.abbreviation;
        const Logo = NBAIcons[Abbr];
        if (!Logo) return null;

        return (
          <div
            key={Abbr}
            style={{ cursor: "pointer", textAlign: "center" }}
            onClick={() => handleClick(Abbr)}
          >
            <Logo size={80} />
            <div style={{ marginTop: "10px", fontSize: "14px", color: "#f9fafb" }}>
              {team.full_name}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<HomePage />);
