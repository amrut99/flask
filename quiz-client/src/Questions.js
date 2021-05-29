import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import logo from './logo.svg';
import {useState} from 'react';
import {useEffect} from 'react';

import Button from '@material-ui/core/Button';
import CssBaseline from '@material-ui/core/CssBaseline';
import TextField from '@material-ui/core/TextField';
import Link from '@material-ui/core/Link';
import Typography from '@material-ui/core/Typography';

import Container from '@material-ui/core/Container';
import Paper from '@material-ui/core/Paper';
import openSocket, { Socket } from "socket.io-client";

import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import FormLabel from '@material-ui/core/FormLabel';

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.secondary,
  },
  footer: {
    padding: theme.spacing(3, 2),
    marginTop: 'auto',
    backgroundColor:
      theme.palette.type === 'light' ? theme.palette.grey[200] : theme.palette.grey[800],
  },
}));
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
export default function Questions() {
  const classes = useStyles();
  const [quizcode, setQuizCode] = useState("");
  const [username, setUsername] = useState("");
  const socket = openSocket("http://localhost:5000");
  const handleUsername = async e => {
    e.preventDefault();
    setUsername(e.target.username.value);
    setQuizCode(e.target.quizcode.value);
    localStorage.setItem('username', e.target.username.value);
  };
 
  const handleSubmit = async e => {
    e.preventDefault();
    // let fdata = new FormData()
    // fdata.append('qcode', quizcode);
    // fdata.append('q', e.target.q.value);
    // fdata.append('file', e.target.file.value);
    // fetch("http://localhost:5000/post-question/"+{quizcode}, 
    // {
    //   method:'POST',
    //   headers:{'Content-Type':'multipart/form-data'},
    //   body:fdata
    // } ).then(res => {
    //   console.log("Done");
    // });
    socket.emit('broadcast', {
          "quiz":quizcode,
          "q":e.target.q.value,
          "c1":e.target.c1.value, 
          "c2":e.target.c2.value, 
          "c3":e.target.c3.value,
          "c4":e.target.c4.value,
          "img":"/static/anand.jpeg"
      });
  };
  if(quizcode && username){
    socket.on('connect', () => {
      socket.emit('join_quiz',{'quiz': quizcode,
        'username':username
      });
    });
    return (
      <div className={classes.root}>
        <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            className={classes.submit}
          >
            Get Next Question
          </Button>
        <form className={classes.root} noValidate autoComplete="off" onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField id="q" label="Question" variant="outlined"/>
          </Grid>
          <Grid item xs={12}>
          <label htmlFor="contained-button-file">
              <input
            accept="image/*"
            className={classes.input}
            id="contained-button-file"
            multiple
            type="file"
          />
          </label>
          </Grid>
          <Grid item xs={6}>
          <TextField id="c1" label="Choice 1" variant="outlined"/>
          </Grid>
          <Grid item xs={6}>
          <TextField id="c2" label="Choice 2" variant="outlined"/>
          </Grid>
          <Grid item xs={6}>
          <TextField id="c3" label="Choice 3" variant="outlined"/>
          </Grid>
          <Grid item xs={6}>
          <TextField id="c4" label="Choice 4" variant="outlined"/>
          </Grid>
          <FormLabel component="legend">Set Right Choice (Answer)</FormLabel>
          <RadioGroup aria-label="Right Choice" name="answer" id="answer">
          <FormControlLabel value="c1" control={<Radio />} label="Choice 1" />
          <FormControlLabel value="c2" control={<Radio />} label="Choice 2" />
          <FormControlLabel value="c3" control={<Radio />} label="Choice 3" />
          <FormControlLabel value="c4" control={<Radio />} label="Choice 4" />
        </RadioGroup>
        <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            className={classes.submit}
          >
            Post Question
          </Button>
        </Grid>
        </form>
        <footer className={classes.footer}>
        <Container maxWidth="sm">
          <Typography variant="body1">Quiz Code:{quizcode} / Username:{username}</Typography>
          <Copyright />
        </Container>
      </footer>
      </div>
    );
  }
  // Autogenerate the quiz code 
    return (
      <div className={classes.root}>
    <Container component="main" className={classes.main} maxWidth="xs">
    <form className={classes.form} onSubmit={handleUsername}>
        <TextField
            variant="outlined"
            margin="normal"
            required
            fullWidth
            autoComplete="off"
            id="quizcode"
            label="This is your quiz code."
            name="quizcode"
            defaultValue={Math.random().toString(36).slice(2)}
            variant="outlined"
          />
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
    </div>
    );
}
