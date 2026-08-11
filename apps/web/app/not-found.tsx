import { ArrowRightIcon, Button, Container, Section } from "@breero/ui";
import Link from "next/link";
export default function NotFound() { return <Section spacing="xl"><Container size="sm"><div className="not-found"><span>404</span><h1>This room looks empty</h1><p>The page may have moved, but we can help you find your way home.</p><Button trailingIcon={<ArrowRightIcon />}>Explore services</Button><Link className="not-found__link" href="/">Return to home</Link></div></Container></Section>; }
