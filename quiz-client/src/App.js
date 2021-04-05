import logo from './logo.svg';
import {useState} from 'react';
import {useEffect} from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import CssBaseline from '@material-ui/core/CssBaseline';
import TextField from '@material-ui/core/TextField';
import Link from '@material-ui/core/Link';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Paper from '@material-ui/core/Paper';
import openSocket from "socket.io-client";

function Copyright() {
  return (
    <Typography variant="body2" color="textSecondary">
      {'Copyright © '}
      <Link color="inherit" href="https://material-ui.com/">
        Your Website
      </Link>{' '}
      {new Date().getFullYear()}
      {'.'}
    </Typography>
  );
}
const useStyles = makeStyles((theme) => ({
  paper: {
    marginTop: theme.spacing(8),
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  avatar: {
    margin: theme.spacing(1),
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: '100%', // Fix IE 11 issue.
    marginTop: theme.spacing(1),
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
  main: {
    marginTop: theme.spacing(8),
    marginBottom: theme.spacing(2),
  },
  footer: {
    padding: theme.spacing(3, 2),
    marginTop: 'auto',
    backgroundColor:
      theme.palette.type === 'light' ? theme.palette.grey[200] : theme.palette.grey[800],
  },
}));

function App() {
  const classes = useStyles();
  const [quizcode, setQuizCode] = useState("");
  const [username, setUsername] = useState("");
  const [answer, setAnswer] = useState("");
  const [question, setQuestion] = useState("");

  const questions = {
    "q":"Who is V. Anand?",
    "a":["cricketer","chess player","Soccer","Tennis"]
  }
  useEffect(() => {
    const socket = openSocket("http://localhost:5000/");

    socket.on('connect', () => {
    console.log("socket connected");
    socket.on('mybroadcast', (data) =>{
        question["q"] = data['q'];
        question["a"] = [data['c1'], data['c2'], data['c3'], data['c4']] 
    });
  });
  }, []);
  
  const handleSubmit = async e => {
    e.preventDefault();
    setQuizCode(e.target.quizcode.value);
    localStorage.setItem('quizcode', e.target.quizcode.value);
  };
  const handleUsername = async e => {
    e.preventDefault();
    setUsername(e.target.username.value);
    localStorage.setItem('username', e.target.username.value);
  };
  const saveAnswer = answer => {
    console.log("Save Answer");
    console.log(answer);
    setAnswer(answer);
  }
  
  const sendans = async e =>{
    console.log(e.target.choice.value);
  }
  const listans = questions.a.map((ans, i) =>
  <Grid item xs={3} ><Button variant="contained" id={i} name={i} color="primary" onClick={(e) => saveAnswer(ans)} >{ans}</Button></Grid>);
  
  if (quizcode && username && answer){
    return (
      <Container component="main" className={classes.main} maxWidth="xs">
        <Typography>Quiz Code:{quizcode}</Typography>
        <Typography>Username:{username}</Typography>
        <Typography>Answer:{answer}</Typography>
        <form className={classes.form} onSubmit={handleUsername}>
            <h1>Correct !!!!!</h1>
        </form>
      </Container>
      );
  }
  if (quizcode && username){
    return (
      <Container component="main" className={classes.main} maxWidth="xs">
        <Typography>Quiz Code:{quizcode}</Typography>
        <Typography>Username:{username}</Typography>
        <form className={classes.form} onSubmit={handleUsername}>
            <h1>Wait for Quiz to Start!!!</h1>
        </form>
      </Container>
      );
  }
  if (quizcode && username && question){
    return(
      <div className={classes.root}>
      <CssBaseline />
      <Container component="main" className={classes.main} maxWidth="sm">
        <Typography variant="h3" component="h2" gutterBottom>
        {questions.q}
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
        <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper className={classes.paper}>
          <img src="https://images.news18.com/ibnlive/uploads/2020/12/1607657713_sports-1.png?impolicy=website&width=534&height=356" />
          </Paper>
        </Grid>
          {listans}
        </Grid>

        </Typography>
      </Container>
      <footer className={classes.footer}>
        <Container maxWidth="sm">
          <Typography variant="body1">Quiz Code:{quizcode} / Username:{username}</Typography>
          <Copyright />
        </Container>
      </footer>
    </div>
    );
  }
// if there's a user show the message below
  if (quizcode) {
    return (
    <Container component="main" className={classes.main} maxWidth="xs">
      <Typography>Quiz Code:{quizcode}</Typography>
      <Typography>Username:{username}</Typography>
    <form className={classes.form} onSubmit={handleUsername}>
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            autoComplete="off"
            id="username"
            label="Enter Username"
            name="username"
            autoFocus
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            className={classes.submit}
          >
            Enter
          </Button>
        </form>
    </Container>
    
    );
  }
  return (
    <Container component="main" className={classes.main} maxWidth="xs">
    <form className={classes.form} onSubmit={handleSubmit}>
          <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            autoComplete="off"
            id="quizcode"
            label="Quiz Code"
            name="quizcode"
            autoFocus
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            className={classes.submit}
          >
            Enter
          </Button>
        </form>
    </Container>
    );
}

export default App;