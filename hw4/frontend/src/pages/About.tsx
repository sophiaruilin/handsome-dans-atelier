// Text from output/site_copy.md (Sophia's approved draft).
export default function About() {
  return (
    <section className="page prose">
      <p className="eyebrow">About Us</p>
      <h1>More than merch. It's a point of connection.</h1>
      <p className="lead">
        Campus Customs is the team behind <strong>Yale Bulldog Blue</strong>, New Haven's shop for officially licensed
        Yale apparel and gifts.
      </p>
      <p>
        We know what a Yale sweatshirt really means. It's the thing you grab before a 9 a.m. seminar, the shirt you wear
        to The Game, and what you pack when you head home for break. When two strangers spot the same bulldog across an
        airport terminal, there's an instant nod: <em>you too?</em> That moment of connection is what we're making.
      </p>
      <p>
        Our collection covers the whole Yale community: students and alumni, athletes and the fans in the stands, all
        twelve residential colleges, the graduate and professional schools, and the parents, grandparents and siblings
        who are proud to say <em>my kid goes to Yale</em>.
      </p>

      <h2>What we stand for</h2>
      <ul className="values">
        <li>
          <strong>Officially licensed.</strong> Authentic Yale marks, done right.
        </li>
        <li>
          <strong>Comfort that lasts.</strong> Casual comfort and classic Bulldog pride, made to outlast your problem
          sets.
        </li>
        <li>
          <strong>Everyone belongs.</strong> If Yale is part of your story, there's something here for you.
        </li>
      </ul>

      <div className="visit-card">
        <h2>Come visit us!</h2>
        <address>
          Yale Bulldog Blue by Campus Customs
          <br />
          57 Broadway, New Haven, CT 06511
        </address>
        <a
          href="https://www.google.com/maps/search/?api=1&query=57+Broadway+New+Haven+CT+06511"
          target="_blank"
          rel="noreferrer"
        >
          Get directions ↗
        </a>
      </div>
    </section>
  )
}
